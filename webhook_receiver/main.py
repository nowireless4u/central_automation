import os
import sys
import datetime
import logging
import json
import asyncio
import base64
import hmac
import hashlib
from deepdiff import DeepDiff
from loguru import logger
from dataclasses import dataclass
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import redis
from typing import Optional
from uuid import UUID
from fastapi import FastAPI, Header, Request, Response
from pydantic import BaseModel
import uvicorn

# Loguru settings
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}")
logger.add("/logs/webhook.log")
logger.add("/logs/webhook_retention.log", retention="5 days")
logger.add("/logs/webhook_rotation.log", rotation="1 MB")
logger.add("/logs/webhook_compressed.log", compression="zip")

# Azure Key vault authentication
VAULT_URL = os.environ["AZURE_KEYVAULT_URL"]
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)

# Redis settings
r_host = client.get_secret('redis-server').value
r_password = client.get_secret('redis-password').value
r = redis.StrictRedis(host=r_host, port=6380, charset='utf-8',
                      password=r_password, ssl=True, decode_responses=True)


class WebhookResponse(BaseModel):
    result: str

class WebhookData(BaseModel):
    id: Optional[str]
    username: Optional[str]
    data: Optional[dict]
    event: Optional[str]
    timestamp: Optional[datetime.datetime]
    model: Optional[str]
    request_id: Optional[UUID]
    alert_type: Optional[str]
    description: Optional[str]
    severity: Optional[str]
    operation: Optional[str]
    details: Optional[dict]
    webhook: Optional[str]
    cluster_hostname: Optional[str]  
   

app = FastAPI(
    title='Webhook Listener',
    description='Universal Webhook Listener',
    version='1.0',
)

# Functions for Netbox Webhook messages
@logger.catch
async def validate_netbox_signature(full_headers, encoded_body):
    netbox_secret = client.get_secret('netbox-secret').value
    logger.info(netbox_secret)
    token = netbox_secret.encode()
    logger.info(token)
    signature = full_headers['X-Hook-Signature']
    logger.info(signature)
    # Create hmac
    encoded_hmac = hmac.new(token, msg=encoded_body, digestmod='sha512')
    logger.info(encoded_hmac)
    if not hmac.compare_digest(
        encoded_hmac.hexdigest(),
        signature
    ):
        logger.info('Invalid CMDB Alert')
        return 'Invalid CMDB Alert'
    elif encoded_hmac.hexdigest() in signature:
        logger.info('Valid CMDB Alert!')
        return 'CMDB Alert Valid'

@logger.catch
async def snapshot_compare(prechange, postchange):
    device_diff = DeepDiff(prechange, postchange, ignore_order=True, exclude_paths={"root['last_updated']"})
    match device_diff:
        case {'values_changed': {"root['name']": {'new_value': new_hostname, 'old_value': old_hostname}}}:
            return {'hostname': new_hostname}
        case {'values_changed': {"root['custom_fields']['central_subscription']": {'new_value': new_subscription, 'old_value': old_subscription}}}:
            return {'central_subscription': new_subscription}
    logger.info(device_diff)
    return device_diff

@logger.catch
async def determine_netbox_message(encoded_body):
    decoded_body = encoded_body.decode('utf-8')
    logger.info(decoded_body)
    body = json.loads(decoded_body)
    logger.info(body)
    match body:
        case {'event': 'updated', 'data': {'serial': serial, 'device_role': {'name': device_type}}}:
            logger.info(f'Device in Netbox has been updated')
            prechange = body['snapshots']['prechange']
            logger.info(f'prechange info sent for compare {prechange}')
            postchange = body['snapshots']['postchange']
            logger.info(f'postchange info sent for compare {postchange}')
            diff = await snapshot_compare(prechange, postchange)
            logger.info(f'This was updated {diff}')
            return {'key': 'cmdb:alert', 'event': 'updated', 'device_type': device_type, 'serial': serial} | diff
        case {'event': event, 'model': 'device', 'data': {'device_type': {'model': model}, 'serial': serial}}:
            logger.info(f'{model} with serial {serial} was {event}')
            return {'key': 'cmdb:alert', 'event': event, 'model': model, 'serial': serial}
        case {'event': event, 'model': 'site', "data": {"name": site_name}}:
            logger.info(f'site {site_name} was {event}')
            return {'key': 'cmdb:alert', 'event': event, 'model': 'site', 'name': site_name}
            
        case _:
            logger.info("Dead end")
            return f"{'DeadEnd'}:{'group'}"

@logger.catch
async def process_netbox_webhook(full_headers, encoded_body):
    validated = await validate_netbox_signature(full_headers, encoded_body)
    logger.info(validated)
    match validated:
        case 'CMDB Alert Valid':
            netbox_message = await determine_netbox_message(encoded_body)
            logger.info(netbox_message)
            return netbox_message
        case _:
            return {'result': 'Webhook Sender not valid'}     


# Functions for Central Webhook messages
@logger.catch
async def validate_central_signature(full_headers, encoded_body):
    cid = full_headers['X-Central-Customer-Id']
    service = full_headers['X-Central-Service']
    delivery = full_headers['X-Central-Delivery-Id']
    timestamp = full_headers['X-Central-Delivery-Timestamp']
    signature = full_headers['X-Central-Signature']
    central_token = client.get_secret(f'central-{cid}-webhooktoken').value
    token = central_token.encode('utf-8')
    # Assign header values to variables
    combined_header = service + delivery + timestamp
    # Decode the encoded body
    decoded_body = encoded_body.decode('utf-8')
    # Combine everything and encode it
    sign_data = str(decoded_body) + str(combined_header)
    sign_data_encoded = sign_data.encode('utf-8')
    # Find Message signature using HMAC algorithm and SHA256 digest mod
    encoded_hmac = hmac.new(token, msg=sign_data_encoded, digestmod=hashlib.sha256).digest()
    generated_signature = base64.b64encode(encoded_hmac).decode()       
    if not hmac.compare_digest(
        signature,
        generated_signature
    ):
        return {'Invalid Central Alert'}
    elif signature in generated_signature:
        logger.info('Central Alert!')
        return 'Central Alert Valid'

@logger.catch
async def determine_central_message(encoded_body):
    decoded_body = encoded_body.decode('utf-8')
    body = json.loads(decoded_body)
    logger.info(body)
    match body:
        case {'alert_type': 'DEVICE_CONFIG_CHANGE_DETECTED', 'details': {'group_name': group_name, 'dev_type': device_type}, "cluster_hostname": cluster}:
            logger.info(f'Config for {group_name} was changed.')
            return {'key': 'config:alert', 'group': group_name, 'device': device_type, 'cluster': cluster}
        case {"alert_type": "New AP detected" | "New Switch connected", "details": {"group_name": group_name, "serial": serial, "dev_type": device_type, }, "cluster_hostname": cluster}:
            logger.info(f"New {device_type} connected to {cluster}")
            return {'key': 'device:alert', 'group': group_name, 'serial': serial, 'device': device_type, 'cluster': cluster}
        case _:
            logger.info('Unsupported Webhook')
            return{'result': 'Unsupported Webhook'}

@logger.catch
async def process_central_webhook(full_headers, encoded_body):
    logger.info(full_headers)
    logger.info(encoded_body)
    validated = await validate_central_signature(full_headers, encoded_body)
    logger.info(validated)
    match validated:
        case 'Central Alert Valid':
            central_message = await determine_central_message(encoded_body)
            logger.info(f"Central message information extracted")
            logger.info(central_message)
            return central_message
        case _:
            return {'result': 'Webhook Sender not valid'} 


@app.post('/webhook', response_model=WebhookResponse, status_code=200)
@logger.catch
async def webhook(
    webhook_input: WebhookData,
    request: Request,
    response: Response,
    content_length: int = Header(...)
):

    if content_length > 1_000_000:
      #  To prevent memory allocation attacks
        response.status_code = 400
        return {'result': 'Content too long'}

    full_headers = request.headers
    logger.info('Full header information')
    logger.info(full_headers)
    encoded_body = await request.body()
    logger.info('Encoded body information')
    logger.info(encoded_body)

    match full_headers:
        case {"X-Central-Signature": signature}:
            logger.info('Aruba Central webhook inbound')
            central_webhook = await process_central_webhook(full_headers, encoded_body)
            alert_info = central_webhook
            key = alert_info.pop('key')
            logger.info(key)
            logger.info(alert_info)
        case {"X-Hook-Signature": signature}:
            logger.info('Netbox webhook inbound')
            netbox_webhook = await process_netbox_webhook(full_headers, encoded_body)
            alert_info = netbox_webhook
            key = alert_info.pop('key')
            logger.info(key)
            logger.info(alert_info)
        case _:
            logger.info('Unknown Webhook Sender')
            return {'result': 'Unknown Webhook Sender'}

    pipe = r.pipeline()
    alert_id = pipe.xadd(key, alert_info, id='*')
    pipe.execute()
    print(f"alert {alert_id} sent")
    return {'result': 'ok'}
    

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=5000)