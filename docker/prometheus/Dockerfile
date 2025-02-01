FROM python:3

WORKDIR /app

COPY docker/prometheus .
COPY pytcs .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "main.py"]