from __future__ import absolute_import

from sentry.utils.imports import import_submodules
from sentry.rules import rules
from sentry.integrations import register

from .notify_action import PagerdutyNotifyServiceAction
from .integration import PagerdutyIntegrationProvider

import_submodules(globals(), __name__, __path__)

rules.add(PagerdutyNotifyServiceAction)
register(PagerdutyIntegrationProvider)
