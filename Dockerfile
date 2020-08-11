## base image
FROM python:3.7.5-slim-buster as base
FROM base as builder
LABEL maintainer="Pritam K Dey <pritamdey@g.harvard.edu"

## install dependencies
#RUN apt-get update && \
#    apt-get upgrade -y && \
#    apt-get install -y netcat-openbsd gcc libpq-dev postgresql-client postgresql-client-common && \
#    apt-get install libspatialindex-dev -y && \
#    apt-get clean
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y netcat-openbsd gcc && \
    apt-get install libspatialindex-dev -y && \
    apt-get clean


## set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYROOT /pyroot
ENV PATH $PYROOT/bin:$PATH
ENV PYTHONUSERBASE $PYROOT

RUN mkdir /app
WORKDIR /app
COPY Pipfile /app/Pipfile
COPY Pipfile.lock /app/Pipfile.lock

RUN pip install --upgrade pip
RUN pip install pipenv
RUN set -ex && PIP_USER=1 pipenv install --system --deploy -v

ADD . /app/

RUN mkdir /app/airpollution/migrations
RUN touch /app/airpollution/migrations/__init__.py

EXPOSE 8000
#CMD sleep 365d

WORKDIR /app
#CMD [ "python", "manage.py runserver 0.0.0.0:8000" ]
ENTRYPOINT ["/app/docker-entrypoint.sh"]
#CMD gunicorn eugreendeal.wsgi:application - bind 0.0.0.0:8000 - workers 3