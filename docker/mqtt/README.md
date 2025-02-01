# MQTT script

This script exports data to MQTT and can be integrated with Home Assistant

## Prerequisites

Set up the `.env` file (as the `.env.example`) with all the required variables for the `pytcs` library and the MQTT broker.


### Docker Compose

A `docker-compose.yml` file is provided to start up the environment

## Home Assistant 

MQTT Sensors configuration:

```yaml
mqtt:
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

  - name: "Program Total"
    unique_id: program_total
    state_topic: "tecnoalarm/programs/total"
    value_template: "{{ 'ON' if value_json.status.status != 0 else 'OFF' }}"
    device_class: running
    device:
      identifiers: tecnoalarm
      name: Alarm
      manufacturer: TecnoAlarm
      model: TP10-42
```