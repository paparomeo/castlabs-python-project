FROM python:alpine
LABEL maintainer="Pedro Romano <pedro@paparomeo.net>"

RUN apk add --no-cache --virtual .build-dependencies build-base libffi-dev openssl-dev

RUN python -m pip install --upgrade pip
RUN pip install gunicorn

WORKDIR /app/

COPY ./requirements.txt /app/

RUN pip install -r requirements.txt

RUN apk del .build-dependencies

COPY . /app/
