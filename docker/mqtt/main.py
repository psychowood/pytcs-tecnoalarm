import time
import os
import json
import paho.mqtt.client as mqtt
from datetime import datetime as dt

from pytcs_tecnoalarm import TCSSession
from pytcs_tecnoalarm.api_models import ZoneStatusEnum
from hamqttmodels import HAMQTTModels

session_key = os.getenv("SESSION_KEY")
app_id = int(os.getenv("APPID"))
serial = os.getenv("SERIAL")
sleep = int(os.getenv("UPDATE_SLEEP_SECONDS","10"))

mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = int(os.getenv("MQTT_PORT"))
mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")
mqtt_qos = int(os.getenv("MQTT_QOS", "0"))
mqtt_retain = os.getenv("MQTT_RETAIN", "true").lower() == "true"

mqtt_ha_autodiscovery_prefix = os.getenv("MQTT_HA_DISCOVERY_PREFIX", None)

programs_allow_enable = os.getenv("PROGRAMS_ALLOW_ENABLE", "false").lower() == "true"
multiple_tcs = os.getenv("MULTIPLE_TCS", "false").lower() == "true"

mqtt_topic_base = "tecnoalarm"
mqtt_topic_centrale = "centrale"
mqtt_topic_zone = "zones"
mqtt_topic_program = "programs"

def clean_name(str):
    return str.replace(" ", "_").replace(".", "_").replace("-", "_").lower()

def log(name, message):
    print(f"{dt.now()} [mqtt-{name}] {message}")

def mqtt_on_message(client, userdata, message):
    log("listener", f"Messagge received: '{message.topic}': {message.payload.decode()}")
    program_name = message.topic.split("/")[-2]
    program_id = programs_ids.get(program_name, 'error')
    if programs_allow_enable:
        if program_id == 'error':
            log("pytcs", "ERROR program not found")
        else:
            payload = message.payload.decode().lower()
            if payload == 'on':
                log("pytcs", f"Enable program '{program_name}' (id={program_id})")
                s.enable_program(program_id)
            elif payload == 'off':
                log("pytcs", f"Disable program '{program_name}' (id={program_id})")
                s.disable_program(program_id)
            else:
                log("pytcs", "ERROR wrong payload")

if __name__ == "__main__":
    log("main", "START")
    s = TCSSession(session_key, app_id)

    log("pytcs", "get_centrali")
    s.get_centrali()
    centrale = s.centrali[serial]

    log("pytcs", "select_centrale")
    s.select_centrale(centrale.tp)

    log("main", "Connect")
    mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttClient.username_pw_set(mqtt_username, mqtt_password)
    mqttClient.connect(mqtt_host, mqtt_port, sleep + 60)

    if multiple_tcs:
        mqtt_topic_base += "/" + serial
        log("main", "Support multiple tcs")

    if programs_allow_enable:
        log("main", "Subscribe to messages")
        mqttClient.on_message = mqtt_on_message
        p = s.get_programs()
        programs_ids = {}
        for programstatus, programdata in zip(p.root, centrale.tp.status.programs):
           if len(programdata.zones) == 0:
               continue

           name = clean_name(programdata.description)
           topic = "{}/{}/{}/set".format(mqtt_topic_base, mqtt_topic_program, name)
           mqttClient.subscribe(topic)
           programs_ids[name] = programdata.idx

    topic = "{}/{}".format(mqtt_topic_base, mqtt_topic_centrale)
    message = centrale.tp.model_dump()
    message['code'] = 'HIDDEN'
    message['passphTCS'] = 'HIDDEN'
    message.pop("status", None)
    log("client", "publish centrale")
    res = mqttClient.publish(topic, json.dumps(message), mqtt_qos, mqtt_retain)

    # Initialize HAMQTTModels instance
    if mqtt_ha_autodiscovery_prefix is not None:
        ha_models = HAMQTTModels(
            serial_number=serial,
            system_type=centrale.model_prefix_map.get(centrale.tp.type, "Unknown"),  # Default to "Unknown"
            description=centrale.tp.description
        )

    mqttClient.loop_start()

    while True:
        log("main", "----------------")
        log("pytcs", "get_zones")
        z = s.get_zones()
        log("client", "publish zones")
        for zone in z.root:
            if zone.status == ZoneStatusEnum.UNKNOWN or not zone.allocated:
                continue

            name = clean_name(zone.description)
            topic = "{}/{}/{}".format(mqtt_topic_base, mqtt_topic_zone, name)
            message = json.dumps(zone.__dict__)
            res = mqttClient.publish(topic, message, mqtt_qos, mqtt_retain)

            # Update HAMQTTModels
            if mqtt_ha_autodiscovery_prefix is not None:
                ha_models.add_zone(
                    zone_id=zone.__dict__['idx'],
                    description=zone.description,
                    topic=topic,
                    allocated=zone.allocated
                )

        # Process programs
        log("pytcs", "get_programs")
        p = s.get_programs()
        log("client", "publish programs")
        for programstatus, programdata in zip(p.root, centrale.tp.status.programs):
            if len(programdata.zones) == 0:
                continue

            name = clean_name(programdata.description)
            status_topic = "{}/{}/{}/status".format(mqtt_topic_base, mqtt_topic_program, name)
            info_topic = "{}/{}/{}/info".format(mqtt_topic_base, mqtt_topic_program, name)
            
            # Publish program info and status
            message = json.dumps(programdata.__dict__)
            res = mqttClient.publish(info_topic, message, mqtt_qos, mqtt_retain)

            message = json.dumps(programstatus.__dict__)
            res = mqttClient.publish(status_topic, message, mqtt_qos, mqtt_retain)
            
            # Update HAMQTTModels
            if mqtt_ha_autodiscovery_prefix is not None:
                ha_models.add_program(
                    program_id=programdata.__dict__['idx'],
                    description=programdata.description,
                    topic=status_topic
                )

        # Handle Home Assistant autodiscovery
        if mqtt_ha_autodiscovery_prefix is not None:
            discovery_messages = ha_models.create_all_discovery_messages(include_programs=True)
            log("autodiscovery payload", json.dumps(discovery_messages))
            
            for topic, message in discovery_messages.items():
                mqttClient.publish(topic, json.dumps(message), mqtt_qos, retain=True)            
            
            mqtt_ha_autodiscovery_prefix = None

        time.sleep(sleep)

    mqttClient.disconnect()
    mqttClient.loop_stop()
