import datetime
import logging

import requests

from typing import Optional, Pattern

from producer.rules import MonitoringRule
from producer.produce import get_producer
from schema_registry.constants import TOPIC


logger = logging.getLogger(__name__)


class MonitoringResult:
    def __init__(
            self, url: str,
            http_status: Optional[int] = None,
            latency: Optional[float] = None,
            meta: Optional[dict] = None,
            regex_match: Optional[bool] = None,
            response: Optional[requests.Response] = None,
    ):
        """

        :param url: url for which request was made
        :param http_status: response HTTP status
        :param latency: time spent on requests
        :param response: related requests.Response object
        :param meta: other meta info
        :param regex_match: Has html response body matched to the
        the expected regex pattern? Defaults to None - to regex check was done.
        """
        self.url = url
        self.http_status = http_status
        self.latency = latency
        self.response = response
        self.regex_match = regex_match
        self.meta = meta

    @property
    def is_success_http_status(self) -> bool:
        return self.http_status is not None and 200 <= self.http_status < 400

    @property
    def is_regex_ok(self) -> bool:
        return self.regex_match is not False

    @property
    def is_success(self) -> bool:
        return self.is_success_http_status and self.is_regex_ok


class SiteChecker:
    def __init__(self, url: str,
                 timeout: float,
                 expected_regex_pattern: Optional[Pattern] = None,
                 ):
        self.url = url
        self.timeout = timeout
        self.expected_regex_pattern = expected_regex_pattern

    def _validate_regex_pattern(self, body: str) -> Optional[bool]:
        if self.expected_regex_pattern is None:
            return None
        return bool(self.expected_regex_pattern.search(body))

    def _request(self) -> requests.Response:
        return requests.get(self.url, timeout=self.timeout)

    def _get_result_from_response(self, response):
        regex_match = self._validate_regex_pattern(response.text)
        latency = response.elapsed.total_seconds()
        http_status = response.status_code
        return MonitoringResult(
            url=self.url,
            http_status=http_status,
            latency=latency,
            regex_match=regex_match,
            response=response,
        )

    def run(self) -> MonitoringResult:
        response, error = None, None
        try:
            response = self._request()
        except requests.RequestException as exc:
            response = exc.response
            error = exc
        finally:
            if response is not None:
                return self._get_result_from_response(response)
            else:
                return MonitoringResult(
                    url=self.url,
                    meta={'exception': error}
                )


def prepare_data_to_report(rule: MonitoringRule,
                           result: MonitoringResult) -> dict:
    return {
        'url': rule.url,
        'rule_name': rule.rule_name,

        'timestamp': datetime.datetime.now(),
        'latency': result.latency,
        'http_status': result.http_status,
        'success': result.is_success_http_status,
        'regex_match': result.regex_match,

        'meta': rule.dict()
    }


def run_check(rule: MonitoringRule):
    logger.debug('Received rule %s', rule)
    checker = SiteChecker(
        url=rule.url,
        timeout=rule.timeout,
        expected_regex_pattern=rule.regex_pattern,
    )
    result = checker.run()
    event_message = prepare_data_to_report(rule, result)
    get_producer().send(
        TOPIC.SiteAvailabilityMonitoring,
        event_message,
    )
