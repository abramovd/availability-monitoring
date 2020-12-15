import datetime

from typing import Optional, Pattern

from pydantic import AnyHttpUrl

from schema_registry.constants import TOPIC
from schema_registry.base import BasePydanticSchema
from schema_registry.registry import register_schema


class BaseMonitoredEvent(BasePydanticSchema):
    pass


class RuleMeta(BasePydanticSchema):
    schedule: Optional[dict]
    timeout: Optional[float]
    regex_pattern: Optional[Pattern] = None


class MonitoredEvent(BaseMonitoredEvent):
    url: AnyHttpUrl
    rule_name: str
    timestamp: datetime.datetime
    latency: Optional[float]
    http_status: Optional[int]
    success: Optional[bool]
    regex_match: Optional[bool]

    meta: RuleMeta


register_schema(
    topic=TOPIC.SiteAvailabilityMonitoring,
    schema=MonitoredEvent,
)
