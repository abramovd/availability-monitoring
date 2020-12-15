import schema_registry  # noqa

from consumer.consume import initialize_consumer
from consumer.storage import initialize_storage
from consumer.config import CONSUMER_CONFIG, STORAGE_CONFIG
from consumer.event_writer import consume_and_write_monitoring_events


def start_consumer():
    initialize_storage(**STORAGE_CONFIG)
    initialize_consumer(**CONSUMER_CONFIG)
    # running in while loop:
    consume_and_write_monitoring_events()


if __name__ == '__main__':
    start_consumer()
