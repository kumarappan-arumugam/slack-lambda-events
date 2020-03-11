from __future__ import absolute_import

from django import forms
from django.utils.translation import ugettext_lazy as _

from sentry.rules.actions.base import EventAction
from sentry.utils import metrics, json
from sentry.models import Integration

from .utils import ( build_alert_payload, LEVEL_TO_SEVERITY )

class PagerdutyNotifyServiceForm(forms.Form):
    service = forms.ChoiceField(choices=(), widget=forms.Select())
    severity = forms.ChoiceField(choices=(), widget=forms.Select())
    tags = forms.CharField(required=False, widget=forms.TextInput())

    def __init__(self, *args, **kwargs):
        # NOTE: Service maps directly to the integration ID
        service_list = [(i.id, i.name) for i in kwargs.pop('integrations')]
        severity = kwargs.pop('severity', None)

        # remove all the extra kwargs before calling super
        super(PagerdutyNotifyServiceForm, self).__init__(*args, **kwargs)

        if service_list:
            self.fields['service'].initial = service_list[0][0]
            self.fields['service'].choices = service_list
            self.fields['service'].widget.choices = self.fields['service'].choices

        if severity:
            self.fields['severity'].initial = severity[0][0]
            self.fields['severity'].choices = severity
            self.fields['severity'].widget.choices = self.fields['severity'].choices


    def clean(self):
        cleaned_data = super(PagerdutyNotifyServiceForm, self).clean()
        service = cleaned_data.get('service', None)

        if not service:
            raise forms.ValidationError(_("Pleade select the service to send alerts to"),
                                        code='invalid'
                                    )

        return cleaned_data

class PagerdutyNotifyServiceAction(EventAction):
    form_cls = PagerdutyNotifyServiceForm
    label = u'Send an alert to the {service} Pagerduty service and show tag(s) {tags} in the alert with {severity} severity'

    def __init__(self, *args, **kwargs):
        super(PagerdutyNotifyServiceAction, self).__init__(*args, **kwargs)
        self.form_fields = {
            'service': {
                'type': 'choice',
                'choices': [(i.id, i.name) for i in self.get_integrations()]
            },
            'severity': {
                'type': 'choice',
                'choices': self.get_severity()
            },
            'tags': {
                'type': 'string',
                'placeholder': 'i.e environment,user,app_name'
            }
        }

    def is_enabled(self):
        return self.get_integrations().exists()

    def after(self, event, state):
        if event.group.is_ignored():
            return

        integration_id = self.get_option('service')
        severity = self.get_option('severity')
        tags = set(self.get_tags_list())

        try:
            integration = Integration.objects.get(
                provider='pagerduty',
                organizations=self.project.organization,
                id=integration_id
            )
        except Integration.DoesNotExist:
            # Integration removed, rule still active.
            return

        def send_alert(event, futures):
            rules = [f.rule for f in futures]
            client = integration.get_installation(organization_id=self.project.organization.id).get_client()
            routing_key = client.api_key
            payload = build_alert_payload(event.group, routing_key, severity, event=event, tags=tags, rules=rules)

            try:
                result = client.EventV2.create(data=payload)
            except Exception as e:
                self.logger.error('rule.fail.pagerduty_post', extra={'error_message': e.message, 'error_class': type(e).__name__})
            else:
                if not result['status'] == 'success':
                    self.logger.error("rule.fail.pagerduty_post", extra={"error": result.get("errors"), "message": result.get("message")})

        key = u'pagerduty:{}'.format(integration_id)

        metrics.incr('alert.sent', instance='pagerduty.alert', skip_internal=False)
        yield self.future(send_alert, key=key)

    def render_label(self):
        try:
            integration_name = Integration.objects.get(
                provider='pagerduty',
                organizations=self.project.organization,
                id=self.get_option('service')
            ).name
        except Integration.DoesNotExist:
            integration_name = '[removed]'

        tags = self.get_tags_list()

        return self.label.format(
            service=integration_name,
            severity=self.get_option('severity') or 'error',
            tags=u'[{}]'.format(', '.join(tags)) if len(tags)>0 else 'no',
        )

    def get_tags_list(self):
        return [s.strip() for s in self.get_option('tags', '').split(',')]

    def get_severity(self):
        return [(v, k) for k, v in LEVEL_TO_SEVERITY.iteritems()]

    def get_integrations(self):
        return Integration.objects.filter(
            provider='pagerduty',
            organizations=self.project.organization,
        )

    def get_form_instance(self):
        return self.form_cls(
            self.data,
            integrations=self.get_integrations(),
            severity=self.get_severity()
        )
