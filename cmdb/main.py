import os
import sys
import asyncio
import redis
import time
import socket
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import usaddress
import operator
import pynetbox
from loguru import logger

consumer=socket.gethostname()
consumer_group = 'cmdb'
stream_key = f'{consumer_group}:alert'

# Loguru settings
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}")
logger.add(f'/logs/{consumer}.log')
logger.add(f'/logs/{consumer}_retention.log', retention="5 days")
logger.add(f'/logs/{consumer}_rotation.log', rotation="1 MB")
logger.add(f'/logs/{consumer}_compressed.log', compression="zip")
logger.info(f'The Consumer name is {consumer} within {consumer_group} and listening to {stream_key}')

# Azure Key vault authentication
VAULT_URL = os.environ["AZURE_KEYVAULT_URL"]
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)

# Redis settings
r_host = client.get_secret('redis-server')
r_password = client.get_secret('redis-password')
r = redis.StrictRedis(host=r_host.value, port=6380, charset='utf-8',
                      password=r_password.value, ssl=True, decode_responses=True)

# Netbox settings
netbox_url = client.get_secret('netbox-url')
netbox_token = client.get_secret('netbox-token')
nb = pynetbox.api(
    netbox_url.value,
    token=netbox_token.value
)
nb.http_session.verify = False

@logger.catch
def get_message_from_response(response):
    return response[0][1][0]

@logger.catch
async def process_ap_message(msg):
    logger.info(msg)
    match msg:
        case {'event': event_type, 'device_type': 'Access Point', 'serial': serial_number}:
            logger.info(f'{device_type} with {serial_number} was {event_type}.')
            device_info = {
                
            }

@logger.catch
async def process_message(msg):
    logger.info(msg)
    match msg:
        case {'event': 'deleted', 'device_type': device_type, 'serial': serial_number}:
            logger.info(f'{device_type} with {serial_number} was deleted.')
            device_info = {
                'event': 'updated',
                'device Type': device_type,
                'serial': serial_number,
                updated_key: updated_value,
            }
            return device_info
        case {'event': 'updated', 'device_type': device_type, 'serial': serial_number}:
            logger.info(f'{device_type} with {serial_number} was updated.')
            updated_key = list(msg.keys())[-1]
            logger.info(updated_key)
            updated_value = msg[next(reversed(msg))]
            logger.info(updated_value)
            device_info = {
                'event': 'updated',
                'device Type': device_type,
                'serial': serial_number,
                updated_key: updated_value,
            }
            return device_info
        case {'event': 'created', 'device_type': device_type, 'serial': serial_number}:
            logger.info(f'{device_type} with {serial_number} was created.')
            device_info = {
                'event': 'updated',
                'device Type': device_type,
                'serial': serial_number,
                updated_key: updated_value,
            }
            return device_info
        case {'event': 'deleted', 'model': 'site', 'name': name}:
            site_info = {
                'event': 'deleted',
                'model': 'site',
                'name': name,
                'worker': 'site'
            }
            logger.info(site_info)
            return site_info
        case {'event': event, 'model': 'site', 'name': name}:
            address = []
            api_attr = f'dcim.sites'
            obj_fltr = 'name'
            site = dict(operator.attrgetter(api_attr)(nb).get(**{obj_fltr: name}))
            physical_address = site['physical_address']
            try:

                address = usaddress.tag(physical_address)[0]
                logger.info(address)
                address_list = []

                breaktags = [
                    'AddressNumber',
                    'StreetNamePreDirectional',
                    'StreetNamePostType',
                    'PlaceName',
                    'StateName',
                    'ZipCode',
                    'CountryName'
                ]

                multibreak = {
                    'AddressNumberPrefix': ['AddressNumber']
                }

                parsed = []
                address_field = ''

                address_items = list(address.items())

                for k, v in address_items:

                    if address_field == '':
                        address_field = k

                    if k in breaktags:

                        breaktags.remove(k)

                        if k in multibreak:
                            for mb in multibreak[k]:
                                if mb in multibreak:
                                    multibreak.remove(mb)

                        address_list = [i for i in address_list if i]

                        if address_list:
                            address_list = ' '.join(address_list)
                            parsed.append(address_list)
                            address['Parsed_' + address_field] = address_list
                            address_field = k

                        address_list = [v]

                    else:

                        address_list.append(v)

                address_list = [i for i in address_list if i]

                if address_list:
                    address_list = ' '.join(address_list)
                    parsed.append(address_list)
                    address['Parsed_' + address_field] = address_list

            # Add combined version of address

                address['Parsed_Address_Complete'] = '\n'.join(parsed)

            # Do a little cleanup, just to be nice

                for k in address:
                    address[k] = address[k].strip()

            # Update addr

                addr = '\r'.join(parsed)

            except KeyError as e:

                address['Error'] = 'Validation Key Error: ' + e.message

            site_address = addr
            logger.info(site_address)
            site_city = f"{address['PlaceName']}"
            site_state = f"{address['StateName']}"
            site_zipcode = f"{address['ZipCode']}"
            site_info = {
                'event': event,
                'name': name,
                'address': site_address,
                'city': site_city,
                'state': site_state,
                'zipcode': site_zipcode,
                'worker': 'site'
            }
            logger.info(site_info)
            return site_info
        case _:
            logger.info("Dead end")
            return f"{'DeadEnd'}::{'group'}"

@logger.catch
async def send_message_to_worker(msg_info):
    alert_info = msg_info
    worker_key = alert_info.pop('worker')
    logger.info(worker_key)
    logger.info(alert_info)
    pipe = r.pipeline()
    alert_id = pipe.xadd(f'{worker_key}:alert', alert_info, id='*')
    pipe.execute()  
    logger.info(f"alert {alert_id} sent")
    
@logger.catch
async def worker():
    try:
        r.xgroup_create(stream_key, consumer_group, mkstream=True)
    except:
        print('Group already exists!')

    while True:
        try:
            response = r.xreadgroup(consumer_group, consumer, {stream_key: '>'}, count=1, block=0)

            if response:
                msg = get_message_from_response(response)
                msg_id = msg[1]
                logger.info(msg_id)
                msg_info = await process_message(msg_id)
                logger.info(msg_info)
                if msg_info:
                    alert = await send_message_to_worker(msg_info)
                    logger.info(alert)
            
            r.xack(stream_key, consumer_group, msg[0])
            logger.info("Stream message ID {} read and processed successfuly by {}".format(msg[0],consumer))
            r.xdel(stream_key, msg[0])
            return {'result': 'ok'}


        except Exception as e:
            print(str(e))
            time.sleep(1)

if __name__ == '__main__':
    asyncio.run(worker())
