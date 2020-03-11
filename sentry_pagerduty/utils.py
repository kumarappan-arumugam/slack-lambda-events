from __future__ import absolute_import

import logging

from sentry import tagstore
from sentry import options
from sentry.models import (
    GroupAssignee, User, Team
)
from sentry.utils.http import absolute_uri
from sentry.utils.assets import get_asset_url

logger = logging.getLogger('sentry.integrations.pagerduty')

LEVEL_TO_SEVERITY = {
    'debug': 'info',
    'info': 'info',
    'warning': 'warning',
    'error': 'error',
    'critical': 'critical',
}

# https://github.com/getsentry/sentry/blob/master/src/sentry/models/group.py#L119
GROUP_STATUS_VERBOSE = {
    0: 'UNRESOLVED',
    1: 'RESOLVED',
    2: 'IGNORED',
    3: 'PENDING_DELETION',
    4: 'DELETION_IN_PROGRESS',
    5: 'PENDING_MERGE'
}

def format_actor_option(actor):
    if isinstance(actor, User):
        return actor.get_display_name()
    if isinstance(actor, Team):
        return actor.slug


def get_assignee(group):
    try:
        assigned_actor = GroupAssignee.objects.get(group=group).assigned_actor()
    except GroupAssignee.DoesNotExist:
        return None

    try:
        return format_actor_option(assigned_actor.resolve())
    except assigned_actor.type.DoesNotExist:
        return None


def build_attachment_title(group, event=None):
    # This is all super event specific and ideally could just use a
    # combination of `group.title` and `group.title + group.culprit`.
    ev_metadata = group.get_event_metadata()
    ev_type = group.get_event_type()
    if ev_type == 'error':
        if 'type' in ev_metadata:
            if group.culprit:
                return u'{} - {}'.format(ev_metadata['type'][:40], group.culprit)
            return ev_metadata['type']
        if group.culprit:
            return u'{} - {}'.format(group.title, group.culprit)
        return group.title
    elif ev_type == 'csp':
        return u'{} - {}'.format(ev_metadata['directive'], ev_metadata['uri'])
    else:
        if group.culprit:
            return u'{} - {}'.format(group.title[:40], group.culprit)
        return group.title


def build_attachment_text(group, event=None):
    # Group and Event both implement get_event_{type,metadata}
    obj = event if event is not None else group
    ev_metadata = obj.get_event_metadata()
    ev_type = obj.get_event_type()

    if ev_type == 'error':
        return ev_metadata.get('value') or ev_metadata.get('function')
    else:
        return None


def build_alert_payload(group, routing_key, severity=None, event=None, tags=None, identity=None, rules=None):

    severity = LEVEL_TO_SEVERITY.get(event.get_tag('level')) if not severity else severity
    description = build_attachment_text(group, event) or ''

    assignee = get_assignee(group)

    fields = []

    if tags:
        event_tags = event.tags if event else group.get_latest_event().tags

        for key, value in event_tags:
            std_key = tagstore.get_standardized_key(key)
            if std_key not in tags:
                continue

            labeled_value = tagstore.get_tag_value_label(key, value)
            fields.append('%s:%s' % (std_key.encode('utf-8'), labeled_value.encode('utf-8')))

    ts = group.last_seen

    if event:
        event_ts = event.datetime
        ts = max(ts, event_ts)

    footer = u'{}'.format(group.qualified_short_id)

    if rules:
        footer += u' via {}'.format(rules[0].label)

        if len(rules) > 1:
            footer += u' (+{} other)'.format(len(rules) - 1)

    logo_url = absolute_uri(get_asset_url('sentry', 'images/sentry-email-avatar.png'))
    status = group.get_status()
    return {
        'payload': {
            'summary': build_attachment_title(group, event),
            'timestamp': ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'source': group.project.name,
            'severity': severity,
            'component': group.culprit,
            'group': group.project.slug,
            'class': group.title,
            'custom_details': {
                'Description': description,
                'Assignee': assignee or 'Not assigned to anyone yet',
                'Sentry ID': str(group.id),
                'Sentry Group': getattr(group, 'message_short', group.message).encode('utf-8'),
                'Checksum': group.checksum,
                'Project ID': group.project.slug,
                'Project Name': group.project.name,
                'Logger': group.logger,
                'Trigerring Rules': footer,
                'Tags': fields,
                'Status': GROUP_STATUS_VERBOSE.get(status, status),
                'Number of times seen': group.times_seen,
                'First seen': group.first_seen.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                'Number of users seen': group.count_users_seen(),
            }
        },
        'images': [{
            'src': logo_url,
            'href': options.get("system.url-prefix"),
            'alt': group.title,
        }],
        'dedup_key': 'sentry-%s-%d' % (group.project.slug, group.id),
        'event_action': 'trigger',
        'client': 'Sentry',
        'client_url': group.get_absolute_url(params={'referrer': 'pagerduty'}),
        'routing_key': routing_key,
    }
