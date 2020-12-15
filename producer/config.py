import os
import logging

from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel


class Config(BaseModel):
    RULES_YAML_DATA_FILE_PATH: Optional[Path]
    PRODUCER_SERVER: str
    PRODUCER_SECURITY_PROTOCOL: str
    PRODUCER_CA_CERTIFICATE: Optional[Path]
    PRODUCER_ACCESS_CERTIFICATE: Optional[Path]
    PRODUCER_ACCESS_KEY: Optional[Path]
    DEFAULT_HTTP_TIMEOUT: int


PRODUCER_IMPLEMENTATION = os.environ.get(
    'PRODUCER_IMPLEMENTATION_CLASS', 'producer.produce.KafkaProducer'
)

config = Config(
    RULES_YAML_DATA_FILE_PATH=os.environ.get(
        'RULES_YAML_DATA_FILE_PATH'
    ),
    PRODUCER_SERVER=os.environ.get('KAFKA_SERVER', 'unknown'),
    PRODUCER_SECURITY_PROTOCOL=os.environ.get(
        'KAFKA_SECURITY_PROTOCOL', 'SSL'),
    PRODUCER_CA_CERTIFICATE=os.environ.get('KAFKA_CA_CERTIFICATE'),
    PRODUCER_ACCESS_CERTIFICATE=os.environ.get('KAFKA_ACCESS_CERTIFICATE'),
    PRODUCER_ACCESS_KEY=os.environ.get('KAFKA_ACCESS_KEY'),
    DEFAULT_HTTP_TIMEOUT=10,
)


PRODUCER_CONFIG: Dict[str, Any] = dict(
    bootstrap_servers=config.PRODUCER_SERVER,
    security_protocol=config.PRODUCER_SECURITY_PROTOCOL,
    ssl_cafile=config.PRODUCER_CA_CERTIFICATE,
    ssl_certfile=config.PRODUCER_ACCESS_CERTIFICATE,
    ssl_keyfile=config.PRODUCER_ACCESS_KEY,
)

logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.DEBUG,
)
