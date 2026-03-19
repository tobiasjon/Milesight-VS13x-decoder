import requests
from requests.auth import HTTPBasicAuth
import logging
import paho.mqtt.client as mqtt
import ssl
import random
import time
import json
from datetime import datetime

import os
from dotenv import load_dotenv
import logging
import signal
import sys
import threading


load_dotenv()
class Config:
    IOTOPEN_MQTT_HOST = os.getenv("IOTOPEN_MQTT_HOST", "mqtt")
    IOTOPEN_MQTT_PORT = int(os.getenv("IOTOPEN_MQTT_PORT", 1883))
    IOTOPEN_MQTT_USERNAME = os.getenv("IOTOPEN_MQTT_USERNAME")
    IOTOPEN_MQTT_PASSWORD = os.getenv("IOTOPEN_MQTT_PASSWORD")
    IOTOPEN_INSTALLATION_ID = int(os.getenv("IOTOPEN_INSTALLATION_ID",0))
    IOTOPEN_CLIENT_ID = int(os.getenv("IOTOPEN_CLIENT_ID",0))
    IOTOPEN_BASEURL = os.getenv("IOTOPEN_BASEURL")



def heartbeat():
    while True:
        logger.info(f"Heartbeat: {sys.argv} is running")
        time.sleep(300)

def handle_signal(sig, frame):
    global running
    logger.info("Shutdown signal received")
    running = False
    sys.exit(0)

def on_connect_iot(client, userdata, flags, rc, properties):
    logger.info("Connected to IoT-Open")
    client.subscribe(f"{Config.IOTOPEN_CLIENT_ID}/+")

def send_values_to_iotopen(client, userdata, msg):
    z2m_values = json.loads(msg.payload.decode())
    #print(f'topic={msg.topic}' )
    logger.info(f'Device updated: {msg.topic}')    
    for z2m_key, z2m_value in z2m_values.items(): 
        logger.debug(f'{z2m_key}={z2m_value}')
        client_iot.publish(f'{Config.IOTOPEN_CLIENT_ID}/obj/z2m/{msg.topic.split("/")[1]}/{z2m_key}',json.dumps(iot_open_value(z2m_value)))

def decode_incomming(client, userdata, msg):
    device = json.loads(msg.payload)
    logger.info(f'{device}')
    device_info=device.get("device_info", {})
    #logger.info(f'mac: {device_info.get("device_mac")}')
    #logger.info(f'name: {device_info.get("device_name")}')
    #logger.info(f'sn: {device_info.get("device_sn")}')
    #logger.info(f'firmware: {device_info.get("firmware_version")}')
    #logger.info(f'hardware: {device_info.get("hardware_version")}')
    #logger.info(f'IP: {device_info.get("ip_address")}')
    #logger.info(f'runningtime: {device_info.get("running_time")}')
    device_exists=iot_create_device(device_info)
    device_id=int(device_exists.get('id'))
    if device.get("line_periodic_data")!=None:
        for line in device.get("line_periodic_data"):
            logger.info(f'{line}')
            iot_create_function('in',device_info, line, device_id)
            iot_create_function('out',device_info, line, device_id)
#            client_iot.publish(f'{Config.IOTOPEN_CLIENT_ID}/{device_info.get("device_mac")}/{line.get("line_uuid")}/in',json.dumps(iot_open_value(line.get("in"))))
#            client_iot.publish(f'{Config.IOTOPEN_CLIENT_ID}/{device_info.get("device_mac")}/{line.get("line_uuid")}/out',json.dumps(iot_open_value(line.get("out"))))
            client_iot.publish(f'{Config.IOTOPEN_CLIENT_ID}/obj/eth/{line.get("line_uuid")}/in',json.dumps(iot_open_value(line.get("in"))))
            client_iot.publish(f'{Config.IOTOPEN_CLIENT_ID}/obj/eth/{line.get("line_uuid")}/out',json.dumps(iot_open_value(line.get("out"))))


def check_devices_in_iotopen(client, userdata, msg):
    devices = json.loads(msg.payload)
    coordinators = []
    end_devices = []
    
    for device in devices:
        if device.get("type") == "Coordinator":
            coordinators.append(device)
        elif device.get("type") == "EndDevice":
            end_devices.append(device)
            #print(device.get("friendly_name"))
            device_exist=iot_create_device(device).json()
            if device_exist!=[]:
                device_id=device_exist.get('id')
            else:
                device_id=0
            definitions = device.get("definition")
            exposes = definitions.get("exposes")
            for value in exposes:
                #print(f'{value.get("name")}')
                logger.debug(iot_create_function(value.get("name"), value.get("property"),device.get("ieee_address"),value, device_id))
    logger.info(f'Coordinators:, {len(coordinators)}')
    logger.info(f'End devices:, {len(end_devices)}')

def iot_create_device(device_info):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "installation_id": Config.IOTOPEN_INSTALLATION_ID,
        "type": 'ethernet',
        "meta": {
            "name": f'{device_info.get("device_name")}',
            "serial_number": f'{device_info.get("device_sn")}',
            "mac_address": f'{device_info.get("device_mac")}',
            "ip": f'{device_info.get("ip_address")}',
            "firmware_version": f'{device_info.get("firmware_version")}',
            "hardware_version": f'{device_info.get("hardware_version")}'
        }
    }
    #print(payload)
    iot_devicexists = requests.get(f"{Config.IOTOPEN_BASEURL}/api/v2/devicex/{Config.IOTOPEN_INSTALLATION_ID}?mac_address={device_info.get('device_mac')}", headers=headers, auth=login,)
    #print(iot_devicexists.json()[0].get('id'))
    if iot_devicexists.json()==[]:
        result = requests.post(f"{Config.IOTOPEN_BASEURL}/api/v2/devicex/{Config.IOTOPEN_INSTALLATION_ID}", headers=headers, auth=login, data=json.dumps(payload) )
        return result.json()
    else:
        #result = requests.put(f"{Config.IOTOPEN_BASEURL}/api/v2/devicex/{Config.IOTOPEN_INSTALLATION_ID}/{iot_devicexists.json()[0].get('id')}", headers=headers, auth=login, data=json.dumps(payload) )
        return iot_devicexists.json()[0]


def iot_create_function(function_name, device, line, device_id):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    topic_read = f'obj/eth/{line.get("line_uuid")}/{function_name}'
    payload = {
        "installation_id": Config.IOTOPEN_INSTALLATION_ID,
        "type": 'counter',
        "meta": {
            "name": f'{device.get("device_name")} - {line.get("line_name")} - {function_name}',
            "topic_read": topic_read,
            "device_id": f'{device_id}',
            "line_uuid": f'{line.get("line_uuid")}' 
        }
    }

    print(payload)
    iot_functionexists = requests.get(f'{Config.IOTOPEN_BASEURL}/api/v2/functionx/{Config.IOTOPEN_INSTALLATION_ID}?topic_read={topic_read}', headers=headers, auth=login)

    if iot_functionexists.json()==[]:
        #print('creating')
        result = requests.post(f"{Config.IOTOPEN_BASEURL}/api/v2/functionx/{Config.IOTOPEN_INSTALLATION_ID}", headers=headers, auth=login, data=json.dumps(payload) )
        return result
    else:
        #print('updating')
        result = requests.put(f"{Config.IOTOPEN_BASEURL}/api/v2/functionx/{Config.IOTOPEN_INSTALLATION_ID}/{iot_functionexists.json()[0].get('id')}", headers=headers, auth=login, data=json.dumps(payload) )
        return result

    
def iot_open_value(value, timestamp=None):
    if timestamp is None:
        timestamp = int(time.time())

    if isinstance(value, dict):
        value = value.get("value")

    if value is None:
        return {"timestamp": timestamp, "value": 0, "msg": "null"}

    if isinstance(value, bool):
        return {"timestamp": timestamp, "value": int(value), "msg": str(value)}

    if isinstance(value, str):
        return {"timestamp": timestamp, "value": 0, "msg": value}

    if isinstance(value, (int, float)):
        return {"timestamp": timestamp, "value": value, "msg": ""}

    return {"timestamp": timestamp, "value": 0, "msg": f"unsupported:{type(value).__name__}"}

def main():
    global login, logger, client_iot, client_z2m, client_id
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logger = logging.getLogger(__name__)

    logger.info('Milesight decoder starting')

    #Only read local .env file for debug. remove when done and use OS environtment inside docker


    login = HTTPBasicAuth(Config.IOTOPEN_MQTT_USERNAME, Config.IOTOPEN_MQTT_PASSWORD)
    # MQTT IoT-Open
    client_id = f'z2m-mqtt-{random.randint(0, 9000)}'
    client_iot = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5, client_id=client_id)
    client_iot.tls_set(certfile=None,
                keyfile=None,
                cert_reqs=ssl.VERIFY_DEFAULT)

    client_iot.username_pw_set(Config.IOTOPEN_MQTT_USERNAME, Config.IOTOPEN_MQTT_PASSWORD)
    client_iot.reconnect_delay_set(1, 60)
    client_iot.on_connect = on_connect_iot
    
    try:
        client_iot.connect(host=Config.IOTOPEN_MQTT_HOST, port=Config.IOTOPEN_MQTT_PORT, clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY)
    except Exception as e:
        logger.warning(f"Error connecting to MQTT broker for Iot-Open ({Config.IOTOPEN_MQTT_HOST}:{Config.IOTOPEN_MQTT_PORT}): {e}")
        sys.exit(1)
    
    running = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    client_iot.message_callback_add(f"{Config.IOTOPEN_CLIENT_ID}/+", decode_incomming)

    client_iot.loop_start()

    #Start heartbeat
    threading.Thread(target=heartbeat, daemon=True).start()

    logger.info('Starting loop')
    while True:
        time.sleep(0.1)
        #print('loop')


#Running
#if __name__ == "__main__":
main()

