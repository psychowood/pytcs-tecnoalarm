# Docker setup

This section contains some ready-made scripts and containerization files to run the library and expose data

## How to build the base image

You can build the base image with

`docker compose build --no-cache`

and get the credentials for your .env running

`docker run -it --rm pytcs-tecnoalarm-base python login.py`

Then use the provided docker-compose.yml to run the services you want:

`docker compose up -d pytcs-tecnoalarm-mqtt`

or

`docker compose up -d pytcs-tecnoalarm-prometheus`

