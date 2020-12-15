import abc
import importlib
import logging
import json

import psycopg2

from typing import Optional, List, Type
from psycopg2.extras import execute_values

from consumer.config import STORAGE_IMPLEMENTATION
from schema_registry.models import MonitoredEvent
from schema_registry.utils import JSONEncoder

logger = logging.getLogger(__name__)


class BaseStorage(abc.ABC):

    def __init__(self, **configs):
        self._configs = configs

    @abc.abstractmethod
    def write_many(self, items: List[MonitoredEvent]):
        pass


class PostgresEventsStorage(BaseStorage):

    def __init__(self, **configs):
        super().__init__(**configs)
        self._connection = psycopg2.connect(**configs)
        self._connection.autocommit = True
        self.try_initialize_table()

    def try_initialize_table(self):
        sql_template = """
        CREATE TABLE IF NOT EXISTS events (
        id           SERIAL PRIMARY KEY,
        created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
        timestamp    TIMESTAMP NOT NULL,
        latency      FLOAT,
        url          TEXT,
        rule_name    TEXT,
        http_status  INTEGER,
        success      BOOLEAN,
        regex_match  BOOLEAN,
        meta         jsonb
        )
        """
        with self._connection.cursor() as curs:
            curs.execute(sql_template)

    def write_many(self, items: List[MonitoredEvent]):
        """Using efficient `psycopg2.extra.execute_values` for bulk insert."""
        sql_template = """
            INSERT INTO events (
                latency, http_status, success, regex_match,
                timestamp, url, rule_name, meta
            )
            VALUES %s
        """
        with self._connection.cursor() as curs:
            execute_values(
                curs, sql_template,
                [
                    (
                        event.latency,
                        event.http_status,
                        event.success,
                        event.regex_match,
                        event.timestamp,
                        event.url,
                        event.rule_name,
                        json.dumps(event.meta.dict(), cls=JSONEncoder),
                    )
                    for event in items],
            )


class MockedEventsStorage(BaseStorage):
    def __init__(self, **configs):
        super().__init__(**configs)
        self._data = []

    def write_many(self, items: List[MonitoredEvent]):
        _items = [event.dict() for event in items]
        logger.info(f'Writing items {_items} to db')
        self._data += _items


_storage: Optional[BaseStorage] = None


def initialize_storage(
        storage_class: Optional[Type[BaseStorage]] = None,
        **config
):
    global _storage
    if storage_class is None:
        module, cls = STORAGE_IMPLEMENTATION.rsplit('.', 1)
        storage_module = importlib.import_module(module)
        storage_class = getattr(storage_module, cls)

    _storage = storage_class(**config)


def get_storage() -> BaseStorage:
    if _storage is None:
        raise RuntimeError('Storage is not initialized')
    return _storage
