FROM python:3.9-alpine3.12 AS base

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

COPY ./Pipfile /app/Pipfile
COPY ./Pipfile.lock /app/Pipfile.lock

WORKDIR /app

RUN pip install pipenv

RUN pipenv install

FROM base AS producer
COPY ./producer /app/producer
COPY ./schema_registry /app/schema_registry
COPY ./configs /app/configs
CMD [ "/bin/sh", "-c", "pipenv run python -m producer.main" ]

FROM base AS consumer
COPY ./consumer /app/consumer
COPY ./schema_registry /app/schema_registry
COPY ./configs /app/configs
CMD [ "/bin/sh", "-c", "pipenv run python -m consumer.main" ]
