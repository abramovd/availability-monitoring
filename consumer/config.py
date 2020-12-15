import os
import logging

from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

from schema_registry.constants import TOPIC


CONSUMER_IMPLEMENTATION = os.environ.get(
    'CONSUMER_IMPLEMENTATION_CLASS',
    'consumer.consume.KafkaConsumer',
)
STORAGE_IMPLEMENTATION = os.environ.get(
    'STORAGE_IMPLEMENTATION_CLASS',
    'consumer.storage.PostgresEventsStorage'
)


class Config(BaseModel):
    CONSUMER_SERVER: Optional[str]
    CONSUMER_SECURITY_PROTOCOL: Optional[str]
    CONSUMER_CA_CERTIFICATE: Optional[Path]
    CONSUMER_ACCESS_CERTIFICATE: Optional[Path]
    CONSUMER_ACCESS_KEY: Optional[Path]
    CONSUMER_SLEEP_INTERVAL_SECONDS: float

    STORAGE_URI: Optional[str]


config = Config(
    CONSUMER_SERVER=os.environ.get('KAFKA_SERVER'),
    CONSUMER_SECURITY_PROTOCOL=os.environ.get(
        'KAFKA_SECURITY_PROTOCOL', 'SSL'),
    CONSUMER_CA_CERTIFICATE=os.environ.get('KAFKA_CA_CERTIFICATE'),
    CONSUMER_ACCESS_CERTIFICATE=os.environ.get('KAFKA_ACCESS_CERTIFICATE'),
    CONSUMER_ACCESS_KEY=os.environ.get('KAFKA_ACCESS_KEY'),
    CONSUMER_SLEEP_INTERVAL_SECONDS=float(
        os.environ.get('CONSUMER_SLEEP_INTERVAL_SECONDS', 2),
    ),

    STORAGE_URI=os.environ.get('POSTGRES_EVENTS_STORAGE_URI'),
)


CONSUMER_CONFIG: Dict[str, Any] = dict(
    topics=[TOPIC.SiteAvailabilityMonitoring, ],
    sleep_interval_seconds=config.CONSUMER_SLEEP_INTERVAL_SECONDS,
    bootstrap_servers=config.CONSUMER_SERVER,
    security_protocol=config.CONSUMER_SECURITY_PROTOCOL,
    ssl_cafile=config.CONSUMER_CA_CERTIFICATE,
    ssl_certfile=config.CONSUMER_ACCESS_CERTIFICATE,
    ssl_keyfile=config.CONSUMER_ACCESS_KEY,

    client_id="availability-monitoring-client-1",
    group_id="availability-monitoring-group-1",
)

STORAGE_CONFIG: Dict[str, Any] = dict(
    dsn=config.STORAGE_URI,
)

logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.DEBUG,
)
