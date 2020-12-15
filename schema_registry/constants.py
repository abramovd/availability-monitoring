from dataclasses import dataclass


@dataclass
class _Topics:
    SiteAvailabilityMonitoring: str


TOPIC = _Topics(
    SiteAvailabilityMonitoring='site-availability-monitoring'
)
