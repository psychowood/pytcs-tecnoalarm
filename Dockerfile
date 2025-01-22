FROM python:3

RUN pip install --no-cache-dir requests pydantic prometheus_client

COPY . .

CMD [ "python", "prome.py"]