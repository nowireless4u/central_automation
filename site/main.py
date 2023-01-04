import os
import sys
import asyncio
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import redis
import time
import socket
from loguru import logger
from pycentral.workflows.workflows_utils import get_conn_from_file
from pycentral.monitoring import Sites

VAULT_URL = os.environ["AZURE_KEYVAULT_URL"]
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)

# Loguru settings
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}")
logger.add("/logs/site.log")
logger.add("/logs/site_retention.log", retention="5 days")
logger.add("/logs/site_rotation.log", rotation="1 MB")
logger.add("/logs/site_compressed.log", compression="zip")

consumer=socket.gethostname()
consumer_group = 'site'
stream_key = f'{consumer_group}:alert'
logger.info(f'The Consumer name is {consumer} within {consumer_group} and listening to {stream_key}')

site = Sites()

@logger.catch
def get_message_from_response(response):
    return response[0][1][0]

@logger.catch
async def process_message(msg):
    central = get_conn_from_file(filename="/creds/central.json", account="us-2")
    logger.info(msg)
    match msg:
        case {'event': 'created', 'name': name, 'address': address, 'city': city, 'state': state, 'zipcode': zipcode,}:
            site_info = {
                "address": address,
                "city": city,
                "state": state,
                "country": "United States",
                "zipcode": zipcode
            }
            logger.info(site_info)
            site_create = site.create_site(conn=central, site_name=f"JA {name}", site_address=site_info)
            logger.info(site_create)
            return f'Site created: {name}'

        case {'event': 'updated', 'name': name, 'address': address, 'city': city, 'state': state, 'zipcode': zipcode,}:
            site_info = {
                "address": address,
                "city": city,
                "state": state,
                "country": "United States",
                "zipcode": zipcode
            }
            site_id = site.find_site_id(conn=central, site_name=f"JA {name}")
            logger.info(site_id)
            site_update = site.update_site(conn=central, site_id=site_id, site_name=f"JA {name}", site_address=site_info)
            logger.info(site_update)
            return f'Site updated: {name}'

        case {'event': 'deleted', 'name': name}:
            site_id = site.find_site_id(conn=central, site_name=f"JA {name}")
            logger.info(site_id)
            site_delete = site.delete_site(conn=central, site_id=site_id)
            logger.info(site_delete)
            return f'Site deleted: {name}'

@logger.catch
async def worker():
    r_host = client.get_secret('redis-server')
    r_password = client.get_secret('redis-password')
    r = redis.StrictRedis(host=r_host.value, port=6380, charset='utf-8',
                          password=r_password.value, ssl=True, decode_responses=True)
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
                if 'Site created:' in msg_info:
                    logger.info(msg_info)
                    logger.info('Site created')
                    r.xack(stream_key, consumer_group, msg[0])
                    logger.info("Stream message ID {} read and processed successfuly by {}".format(msg[0],consumer))
                    r.xdel(stream_key, msg[0])
                    return {'result': 'ok'}
                elif 'Site updated:' in msg_info:
                    logger.info(msg_info)
                    logger.info('Site updated')
                    r.xack(stream_key, consumer_group, msg[0])
                    logger.info("Stream message ID {} read and processed successfuly by {}".format(msg[0],consumer))
                    r.xdel(stream_key, msg[0])
                    return {'result': 'ok'} 
                elif 'Site deleted:' in msg_info:
                    logger.info(msg_info)
                    logger.info('Site deleted')
                    r.xack(stream_key, consumer_group, msg[0])
                    logger.info("Stream message ID {} read and processed successfuly by {}".format(msg[0],consumer))
                    r.xdel(stream_key, msg[0])
                    return {'result': 'ok'}       
                else:
                    logger.info(msg_info)
                    logger.info('Match fell through')
                    r.xack(stream_key, consumer_group, msg[0])
                    logger.info("Stream message ID {} read and processed successfuly by {}".format(msg[0],consumer))
                    r.xdel(stream_key, msg[0]) 
                    return {'result': 'ok'}


        except Exception as e:
            print(str(e))
            time.sleep(1)

if __name__ == '__main__':
    asyncio.run(worker())