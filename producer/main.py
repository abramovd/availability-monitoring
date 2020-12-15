import schema_registry  # noqa

from producer.scheduler import run_periodic_rules
from producer.rules import get_monitoring_rules
from producer.produce import initialize_producer
from producer.config import config, PRODUCER_CONFIG


def start_producer():
    initialize_producer(**PRODUCER_CONFIG)
    rules = get_monitoring_rules(config.RULES_YAML_DATA_FILE_PATH)
    run_periodic_rules(rules)


if __name__ == '__main__':
    start_producer()
