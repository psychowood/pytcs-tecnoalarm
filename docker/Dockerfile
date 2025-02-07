FROM python:3-alpine AS pytcs-tecnoalarm-base

# Override the repo running
# docker build --build-arg SRC_REPO=http://your-repo -t pytcs-tecnoalarm .
# or within the docker compose file

ARG SRC_REPO="https://github.com/icovada/pytcs-tecnoalarm"
RUN echo "Using repository $SRC_REPO"

RUN apk --no-cache --update add git
RUN adduser -D pytcs-user

RUN mkdir -p /app
RUN chown pytcs-user /app
USER pytcs-user

WORKDIR /app

RUN git clone $SRC_REPO pytcs-tecnoalarm

# Build the library
RUN pip install --no-cache-dir ./pytcs-tecnoalarm

WORKDIR /app/pytcs-tecnoalarm

CMD ["echo", "You can get your Session token and App ID via 'docker run -it --rm pytcs-tecnoalarm-base python login.py'"]
