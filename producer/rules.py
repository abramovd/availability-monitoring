import abc
import yaml

from pathlib import Path
from pydantic import BaseModel, AnyHttpUrl
from typing import Optional, Pattern, List
from producer.config import config


class IntervalSchedule(BaseModel):
    weeks: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0


class Schedule(BaseModel):
    interval: IntervalSchedule


class MonitoringRule(BaseModel):
    rule_name: str
    url: AnyHttpUrl
    schedule: Schedule
    timeout: float = config.DEFAULT_HTTP_TIMEOUT
    regex_pattern: Optional[Pattern] = None

    def __str__(self):
        return self.rule_name


class BaseRulesLoader(abc.ABC):
    def get_monitoring_rules(self) -> List[MonitoringRule]:
        data = self.load_data()
        return [
            MonitoringRule(rule_name=rule_name, **meta)
            for rule_name, meta in data.items()
        ]

    @abc.abstractmethod
    def load_data(self) -> dict:
        pass


class YamlDataLoader(BaseRulesLoader):

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load_data(self):
        with open(self.file_path) as f:
            data = yaml.safe_load(f)
        return data


def get_monitoring_rules(file_path: Path) -> List[MonitoringRule]:
    return YamlDataLoader(file_path).get_monitoring_rules()
