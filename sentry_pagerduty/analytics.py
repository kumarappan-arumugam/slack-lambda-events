from __future__ import absolute_import, print_function

from sentry import analytics


class PagerdutyIntegrationAssign(analytics.Event):
    type = 'integrations.pagerduty.assign'

    attributes = (
        analytics.Attribute('actor_id', required=False),
    )


class PagerdutyIntegrationStatus(analytics.Event):
    type = 'integrations.pagerduty.status'

    attributes = (
        analytics.Attribute('status'),
        analytics.Attribute('resolve_type', required=False),
        analytics.Attribute('actor_id', required=False),
    )


analytics.register(PagerdutyIntegrationAssign)
analytics.register(PagerdutyIntegrationStatus)
