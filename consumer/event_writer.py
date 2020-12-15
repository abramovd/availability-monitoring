import logging

from consumer.consume import get_consumer
from consumer.storage import get_storage
from schema_registry.constants import TOPIC


logger = logging.getLogger(__name__)


def consume_and_write_monitoring_events():
    for topic, messages in get_consumer().run():
        if topic != TOPIC.SiteAvailabilityMonitoring:
            logger.info('Received not a monitoring event.')
            continue

        get_storage().write_many(messages)
