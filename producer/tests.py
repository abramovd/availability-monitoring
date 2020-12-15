import datetime
import unittest

import requests
import responses

from pathlib import Path

from pydantic import ValidationError

from producer.produce import initialize_producer, get_producer, MockedProducer
from schema_registry.constants import TOPIC
from schema_registry.models import MonitoredEvent
from schema_registry.exceptions import SchemaNotFound
from producer.rules import MonitoringRule, get_monitoring_rules
from producer.checker import SiteChecker, MonitoringResult


def get_fake_payload() -> dict:
    return dict(
        url='http://localhost',
        rule_name='fake-rule',
        meta={'timeout': 10},
        timestamp=datetime.datetime(2020, 12, 13, 10, 0, 0),
        latency=0.25,
        http_status=200,
        success=True,
    )


def create_monitoring_rule(
    rule_name='test-rule',
    url='http://localhost:8000/test/',
    timeout=10,
    schedule=None,
    regex_pattern=None,
) -> MonitoringRule:
    schedule = schedule or {'interval': {'seconds': 10}}
    return MonitoringRule(
        rule_name=rule_name,
        url=url,
        timeout=timeout,
        schedule=schedule,
        regex_pattern=regex_pattern,
    )


class ProducerTest(unittest.TestCase):
    def setUp(self):
        initialize_producer(MockedProducer)

    def test_consumer_initialized_globally_with_config(self):
        initialize_producer(MockedProducer, test_config='test-config')
        producer = get_producer()

        self.assertIsInstance(producer, MockedProducer)
        self.assertEqual(producer._configs, dict(test_config='test-config'))

    def test_send_message__success(self):
        producer = get_producer()
        payload = get_fake_payload()

        producer.send(TOPIC.SiteAvailabilityMonitoring, message=payload)

        self.assertEqual(
            producer._sent_data,
            [(TOPIC.SiteAvailabilityMonitoring, MonitoredEvent(**payload)), ]
        )

    def test_send_message__not_existing_schema_for_topic(self):
        producer = get_producer()
        payload = get_fake_payload()

        with self.assertRaises(SchemaNotFound):
            producer.send('random-topic', message=payload)

    def test_send_message__schema_validationerror(self):
        producer = get_producer()

        with self.assertRaises(ValidationError):
            producer.send(
                TOPIC.SiteAvailabilityMonitoring,
                message={'test': 'test'},
            )


class RulesLoaderTest(unittest.TestCase):

    yaml_fixture_path = Path('producer/sites.yaml')

    def test_load_rules_from_yaml__success(self):
        rules = get_monitoring_rules(self.yaml_fixture_path)

        self.assertEqual(len(rules), 3)
        self.assertEqual(
            rules[2],
            MonitoringRule(
                rule_name='aiven-try-free',
                url='https://aiven.io/',
                timeout=10,
                schedule={'interval': {'seconds': 10}},
                regex_pattern='Try (Now For )?Free',
            )
        )


class SiteCheckerTest(unittest.TestCase):
    @responses.activate
    def test_site_check_success_200(self):
        url = 'http://localhost:8000/test/'
        rule = create_monitoring_rule(url=url)
        responses.add(responses.GET, url, body='OK', status=200)

        result = SiteChecker(
            url=rule.url, timeout=rule.timeout,
            expected_regex_pattern=rule.regex_pattern,
        ).run()

        self.assertIsInstance(result, MonitoringResult)
        self.assertTrue(result.is_success)
        self.assertTrue(result.is_regex_ok)

        self.assertEqual(str(result.url), url)
        self.assertEqual(result.http_status, 200)
        self.assertIsInstance(result.latency, float)

    @responses.activate
    def test_site_check_regex_match__success(self):
        url = 'http://localhost:8000/test/'
        rule = create_monitoring_rule(
            url=url, regex_pattern='Try (Now For )?Free',
        )
        responses.add(responses.GET, url, body='Try Free', status=200)

        result = SiteChecker(
            url=rule.url, timeout=rule.timeout,
            expected_regex_pattern=rule.regex_pattern,
        ).run()

        self.assertIsInstance(result, MonitoringResult)
        self.assertTrue(result.is_success)
        self.assertTrue(result.is_regex_ok)

        self.assertEqual(str(result.url), url)
        self.assertEqual(result.http_status, 200)
        self.assertIsInstance(result.latency, float)

    @responses.activate
    def test_site_check_regex_mismatch(self):
        url = 'http://localhost:8000/test/'
        rule = create_monitoring_rule(
            url=url, regex_pattern='Try (Now For )?Free',
        )
        responses.add(responses.GET, url, body='Hello', status=200)

        result = SiteChecker(
            url=rule.url, timeout=rule.timeout,
            expected_regex_pattern=rule.regex_pattern,
        ).run()

        self.assertIsInstance(result, MonitoringResult)
        self.assertFalse(result.is_success)
        self.assertFalse(result.is_regex_ok)

        self.assertEqual(str(result.url), url)
        self.assertEqual(result.http_status, 200)
        self.assertIsInstance(result.latency, float)

    @responses.activate
    def test_site_check_timeout(self):
        url = 'http://localhost:8000/test/'
        rule = create_monitoring_rule(url=url)
        timeout_exception = requests.exceptions.Timeout('timeoit')
        responses.add(responses.GET, url, body=timeout_exception)

        result = SiteChecker(
            url=rule.url, timeout=rule.timeout,
            expected_regex_pattern=rule.regex_pattern,
        ).run()

        self.assertIsInstance(result, MonitoringResult)
        self.assertFalse(result.is_success)

        self.assertEqual(str(result.url), url)
        self.assertIsNone(result.http_status, None)
        self.assertIsNone(result.latency)
        self.assertEqual(
            result.meta, {'exception': timeout_exception},
        )
