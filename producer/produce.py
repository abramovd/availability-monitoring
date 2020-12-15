import abc
import importlib
import logging

from typing import Optional, Dict, List, Type

from kafka import KafkaProducer as _KafkaProducer

from producer.config import PRODUCER_IMPLEMENTATION
from schema_registry.registry import get_schema
from schema_registry.registry import BasePydanticSchema
from schema_registry.utils import pydantic_to_json_serializer


logger = logging.getLogger(__name__)


class BaseProducer(abc.ABC):
    def __init__(self, **configs):
        self._configs = configs

    @staticmethod
    def get_validated_message(message_type: str,
                              message: Dict) -> BasePydanticSchema:
        schema = get_schema(topic=message_type)
        return schema(**message)

    @abc.abstractmethod
    def send(self, message_type: str, message: Dict, **kwargs):
        pass


class KafkaProducer(BaseProducer):
    def __init__(self, **configs):
        super(KafkaProducer, self).__init__(**configs)
        self._producer = _KafkaProducer(
            value_serializer=pydantic_to_json_serializer,
            **configs
        )

    def send(self, message_type: str, message: Dict, **kwargs):
        parsed_message = self.get_validated_message(message_type, message)
        self._producer.send(
            topic=message_type,
            value=parsed_message,
        )


class MockedProducer(BaseProducer):

    def __init__(self, **configs):
        super(MockedProducer, self).__init__(**configs)
        self._sent_data: List[(str, BasePydanticSchema)] = []

    def send(self, message_type: str, message: Dict, **kwargs):
        parsed_message = self.get_validated_message(message_type, message)
        logger.debug(
            f'Fake sending message from producer {message_type}: '
            f'{parsed_message}'
        )
        self._sent_data.append((message_type, parsed_message))


_producer: Optional[BaseProducer] = None


def initialize_producer(producer_class: Optional[Type[BaseProducer]] = None,
                        **config):
    global _producer
    if producer_class is None:
        module, cls = PRODUCER_IMPLEMENTATION.rsplit('.', 1)
        producer_module = importlib.import_module(module)
        producer_class = getattr(producer_module, cls)

    _producer = producer_class(**config)


def get_producer() -> BaseProducer:
    if _producer is None:
        raise RuntimeError('Producer is not initialized')
    return _producer
