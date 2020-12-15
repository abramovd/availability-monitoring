import unittest

from unittest import mock

from consumer.consume import initialize_consumer, get_consumer, MockedConsumer
from consumer.storage import initialize_storage, get_storage, \
    MockedEventsStorage
from consumer.main import start_consumer
from schema_registry.models import MonitoredEvent
from schema_registry.constants import TOPIC

TIMEOUT_CONSUMER_MS = 5
SLEEP_INTERVAL = (TIMEOUT_CONSUMER_MS + 2) / 1000.0
MOCKED_CONSUMER_CONFIG = {
    'topics': ['test', ],
    # this config should run poll one time only
    'sleep_interval_seconds': SLEEP_INTERVAL,
    'timeout_ms': TIMEOUT_CONSUMER_MS,
    'custom_config_var': 'test',
}


class ConsumerTest(unittest.TestCase):

    def setUp(self):
        initialize_consumer(
            MockedConsumer,
            **MOCKED_CONSUMER_CONFIG
        )

    def test_consumer_initialized_globally_with_config(self):
        initialize_consumer(
            MockedConsumer,
            **MOCKED_CONSUMER_CONFIG
        )

        consumer = get_consumer()

        self.assertIsInstance(consumer, MockedConsumer)
        self.assertEqual(consumer._configs, {'custom_config_var': 'test'})
        self.assertEqual(consumer._sleep_interval_seconds, SLEEP_INTERVAL)
        self.assertEqual(consumer._timeout_ms, TIMEOUT_CONSUMER_MS)

    def test_consumer_poll(self):
        consumer = get_consumer()

        result = consumer.poll()
        self.maxDiff = None
        self.assertEqual(
            result,
            {
                TOPIC.SiteAvailabilityMonitoring: [
                    MockedConsumer.get_fake_payload(),
                ],
            }
        )

    def test_consumer__run_success(self):
        consumer = get_consumer()

        batches = list(consumer.run())

        self.assertEqual(len(batches), 1)
        topic, messages = batches[0]
        self.assertEqual(topic, TOPIC.SiteAvailabilityMonitoring)
        self.assertEqual(len(messages), 1)
        self.maxDiff = None
        self.assertEqual(
            messages[0],
            MonitoredEvent(**MockedConsumer.get_fake_payload())
        )

    @mock.patch(
        'consumer.consume.MockedConsumer.poll',
        mock.MagicMock(
            return_value={
                TOPIC.SiteAvailabilityMonitoring:
                    [
                        mock.MagicMock(return_value={'bad_key': 'bad_value'}),
                        MockedConsumer.get_fake_payload(),
                    ]
            }
        )
    )
    def test__consumer__run__data_validation__logged_exception(self):
        consumer = get_consumer()

        with mock.patch('consumer.consume.logger') as logger_mock:
            batches = list(consumer.run())

        self.assertEqual(len(batches), 1)
        logger_mock.exception.assert_called_once_with(
            f'Validation error for message against {MonitoredEvent}'
        )


class StorageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(StorageTest, cls).setUpClass()
        initialize_storage(MockedEventsStorage, test_config='test-config')

    def test_storage_initialized_globally_with_config(self):
        storage = get_storage()

        self.assertIsInstance(storage, MockedEventsStorage)
        self.assertEqual(storage._configs, {'test_config': 'test-config'})

    def test_write_many(self):
        storage = get_storage()
        fake_event = MonitoredEvent(**MockedConsumer.get_fake_payload())

        storage.write_many([fake_event, fake_event, ])

        self.assertEqual(
            storage._data, [fake_event.dict(), fake_event.dict(), ]
        )


@mock.patch(
    'consumer.main.CONSUMER_CONFIG',
    MOCKED_CONSUMER_CONFIG,
)
@mock.patch(
    'consumer.storage.STORAGE_IMPLEMENTATION',
    'consumer.storage.MockedEventsStorage',
)
@mock.patch(
    'consumer.consume.CONSUMER_IMPLEMENTATION',
    'consumer.consume.MockedConsumer',
)
class ConsumerIntegrationTest(unittest.TestCase):
    def test_write_consumed_events(self):
        fake_event = MonitoredEvent(**MockedConsumer.get_fake_payload())

        start_consumer()

        storage = get_storage()
        self.assertEqual(
            storage._data, [fake_event.dict(), ]
        )
