import abc
import datetime
import importlib
import logging
import time

from typing import Optional, Type, Tuple, List, Dict, Generator

from kafka import KafkaConsumer as _KafkaConsumer

from consumer.config import CONSUMER_IMPLEMENTATION
from schema_registry import get_schema
from schema_registry.base import BasePydanticSchema
from schema_registry.constants import TOPIC
from schema_registry.exceptions import SchemaNotFound
from schema_registry.utils import json_to_dict


logger = logging.getLogger(__name__)


class BaseConsumer(abc.ABC):
    def __init__(self,
                 topics: List[str],
                 sleep_interval_seconds: float,
                 timeout_ms: float = float('inf'),
                 **configs):
        self._topics = topics
        self._timeout_ms = timeout_ms
        self._sleep_interval_seconds = sleep_interval_seconds
        self._configs = configs

    @abc.abstractmethod
    def poll(self, **kwargs) -> Dict[str, List[Dict]]:
        pass

    @staticmethod
    def _parse_messages(
            schema: Type[BasePydanticSchema],
            messages: List[Dict],
    ) -> List[BasePydanticSchema]:
        parsed_messages = []
        for message in messages:
            try:
                parsed_message = schema(**message)
                parsed_messages.append(parsed_message)
            except Exception:
                logger.exception(
                    f'Validation error for message against {schema}'
                )
        return parsed_messages

    def run(
            self, **poll_kwargs
    ) -> Generator[Tuple[str, List[BasePydanticSchema]], None, None]:
        consumer_timeout = time.time() + (self._timeout_ms / 1000.0)
        while time.time() < consumer_timeout:
            for topic, messages in self.poll(**poll_kwargs).items():
                try:
                    schema = get_schema(topic)
                except SchemaNotFound:
                    logger.exception(f'Schema not found for topic {topic}')
                    continue
                parsed_messages = self._parse_messages(schema, messages)
                yield topic, parsed_messages
            time.sleep(self._sleep_interval_seconds)


class KafkaConsumer(BaseConsumer):
    def __init__(self,
                 topics: List[str],
                 sleep_interval_seconds: float,
                 timeout_ms: float = float('inf'),
                 **configs):
        super(KafkaConsumer, self).__init__(
            topics,
            sleep_interval_seconds,
            timeout_ms,
            **configs
        )
        self._consumer = _KafkaConsumer(
            value_deserializer=json_to_dict,
            **configs
        )
        self._consumer.subscribe(topics)

    def poll(self, **kwargs) -> Dict[str, List[Dict]]:
        return {
            topic.topic: [message.value for message in messages]
            for topic, messages in self._consumer.poll(**kwargs).items()
        }


class MockedConsumer(BaseConsumer):

    @staticmethod
    def get_fake_payload() -> Dict:
        return dict(
            url='http://localhost',
            rule_name='fake-rule',
            meta={'timeout': 10},
            timestamp=datetime.datetime(2020, 12, 13, 10, 0, 0),
            latency=0.25,
            http_status=200,
            success=True,
        )

    def poll(self, **kwargs) -> Dict[str, List[Dict]]:
        logger.info('Poll from MockedConsumer')
        return {
            TOPIC.SiteAvailabilityMonitoring: [
                self.get_fake_payload(),
            ],
        }


_consumer: Optional[BaseConsumer] = None


def initialize_consumer(consumer_class: Optional[Type[BaseConsumer]] = None,
                        **config):
    global _consumer
    if consumer_class is None:
        module, cls = CONSUMER_IMPLEMENTATION.rsplit('.', 1)
        consumer_module = importlib.import_module(module)
        consumer_class = getattr(consumer_module, cls)

    _consumer = consumer_class(**config)


def get_consumer() -> BaseConsumer:
    if _consumer is None:
        raise RuntimeError('Consumer is not initialized')
    return _consumer
