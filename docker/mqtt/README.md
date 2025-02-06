# MQTT script

This script exports data to MQTT and can be integrated with Home Assistant

## Prerequisites

Set up the `.env` file (as the `.env.example`) with all the required variables for the `pytcs` library and the MQTT broker.


### Docker Compose

A `docker-compose.yml` file is provided to start up the environment.

Build (only the first time): `docker compose build tecnoalarm`

Run: `docker compose up -d`

## Home Assistant 

MQTT Sensors configuration:

```yaml
mqtt:
  - binary_sensor:
      - name: "Room window"
        unique_id: room_window
        state_topic: "tecnoalarm/zones/room_window"
        value_template: "{{ 'ON' if value_json.status == 'OPEN' else 'OFF' }}"
        device_class: window
        device:
          identifiers: tecnoalarm
          name: Alarm
          manufacturer: TecnoAlarm
          model: TP10-42
    
  - switch:
      - name: "Program Total"
        unique_id: program_total
        state_topic: "tecnoalarm/programs/total/status"
        value_template: "{{ 'ON' if value_json.status != 0 else 'OFF' }}"
        command_topic: "tecnoalarm/programs/total/set"
        payload_on: "ON"
        payload_off: "OFF"
        device:
          identifiers: tecnoalarm
          name: Alarm
          manufacturer: TecnoAlarm
          model: TP10-42
```