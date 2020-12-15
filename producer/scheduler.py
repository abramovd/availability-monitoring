from typing import List

from apscheduler.schedulers.blocking import BlockingScheduler
from producer.rules import MonitoringRule
from producer.checker import run_check


def _run_monitoring_rule(rule: MonitoringRule) -> None:
    run_check(rule)


def run_periodic_rules(rules: List[MonitoringRule]) -> None:
    scheduler = BlockingScheduler()
    for rule in rules:
        if rule.schedule.interval is None:
            raise RuntimeError(
                f'Interval schedule must be defined for all rules: {rule}'
            )
        scheduler.add_job(
            _run_monitoring_rule,
            kwargs={'rule': rule},
            trigger='interval',
            **rule.schedule.interval.dict()
        )
    scheduler.start()
