# Python library to interface with myTecnoalarm TCS app cloud services

This repo provides code to interface with the cloud services of the "my Tecnoalarm TCS" app.
Funcionality has been reverse-engineered and may not be complete.

## How to use it

To use this library you need to authenticate to the cloud service.

### First login

Open an interactive prompt and run:

```python
from tcsession import TCSSession
s = TCSSession()
s.login(email, password)
```

If your account does not have 2 factor authenticator, you will be logged in.
Otherwise, this will throw an `OTPException`

Get the code from your email and run

```python
s.login(email, password, pin)
```

If everything goes right, you will have an authenticated token and app-id to re-use in the future
(does not seem to expire)

extract then with

```python
s.token
s.appid
```

### Future logins

Simply pass your token and appid when instantiating the session

```python
from tcsession import TCSSession
s = TCSSession(token, appid)
```

This will run the `.re_auth()` function that should re-enable the token for immediate use.

The token never changes.

## Docker & MQTT

Set up the `.env` file (as the `.env.example`) with all the required variables for the `pytcs` library and the MQTT broker.

### Docker Compose

Create the container by adding the following service to the `docker-compose.yaml` (e.g. this project is cloned in the `pytcs` subfolder):
```yaml
services:
    tecnoalarm:
        container_name: tecnoalarm
        build:
            context: pytcs
            dockerfile: ./docker/mqtt/Dockerfile
        env_file: pytcs/.env
        restart: unless-stopped
```

Build (needed only the first time) & run:
```shell
docker compose up -d --no-deps --build tecnoalarm
```

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