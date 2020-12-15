from typing import Dict, Type

from schema_registry.exceptions import SchemaAlreadyRegistered, SchemaNotFound
from schema_registry.base import BasePydanticSchema


_SCHEMA_REGISTRY_MAP: Dict[str, Type[BasePydanticSchema]] = {}


def get_schema(topic: str) -> Type[BasePydanticSchema]:
    schema = _SCHEMA_REGISTRY_MAP.get(topic)
    if schema is None:
        raise SchemaNotFound(f'No schemas for topic {topic}')
    return schema


def register_schema(topic: str, schema: Type[BasePydanticSchema]):
    _existing_schema = _SCHEMA_REGISTRY_MAP.get('topic')
    if _existing_schema is not None:
        raise SchemaAlreadyRegistered(
            f'Schema already registered for topic {topic}'
        )
    _SCHEMA_REGISTRY_MAP[topic] = schema
