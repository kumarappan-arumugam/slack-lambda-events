# -*- coding: utf-8 -*-
from __future__ import print_function

# python in-built imports
import hmac
import json
import os
import platform
import sys

# third-party imports
from pyee import AsyncIOEventEmitter

# local imports
from .version import __version__

_ACCEPTED_EVENT_TYPES = ['messages.channel']

class SlackEventsException(Exception):
    """
    Base exception for all errors raised by the SlackClient library
    """
    def __init__(self, msg=None):
        if msg is None:
            # default error message
            msg = "An error occurred in the SlackEventsAdapter"
        super(SlackEventException, self).__init__(msg)

class SlackEventsAdapter(AsyncIOEventEmitter):
    """The slack event request body (https://api.slack.com/events-api#receiving_events)"""

    def __init__(self, request, signing_secret, app_id, accepted_event_types=_ACCEPTED_EVENT_TYPES):
        AsyncIOEventEmitter.__init__(self)
        self.app_id = app_id
        self.request = request
        self.event = request['body']
        self.signing_secret = signing_secret
        self.package_info = self.get_package_info()
        self.accepted_event_types = accepted_event_types

    # def verifyAuth(self):
    #     try:
    #         # User not included in all events as not all events are controlled by users
    #         return self.event.event.user and self.event.event.user in self.event.authed_users
    #     except AttributeError:
    #         return False

    def make_response(self, message='', code=200, statusDescription='', isBase64Encoded=False, multiValueHeaders=None):

        def is_json():
            try:
                json_object = json.loads(message)
            except json.decoder.JSONDecodeError:
                return False
            return True

        # set right headers
        if multiValueHeaders is None:
            multiValueHeaders = {'X-Slack-Powered-By': [self.package_info]}
        else:
            multiValueHeaders['X-Slack-Powered-By'] = [self.package_info]
        if is_json():
            multiValueHeaders['Content-Type'] = ["application/json"]
            multiValueHeaders['Set-cookie'] = ["cookies"]

        if code == 200:
            statusDescription = '200 OK'

        return dict(statusCode=code,
                    statusDescription=statusDescription,
                    isBase64Encoded=isBase64Encoded,
                    multiValueHeaders=multiValueHeaders,
                    body=message)

    def get_package_info(self):
        client_name = __name__.split('.')[0]
        client_version = __version__  # Version is returned from version.py

        # Collect the package info, Python version and OS version.
        package_info = {
            "client": "{0}/{1}".format(client_name, client_version),
            "python": "Python/{v.major}.{v.minor}.{v.micro}".format(v=sys.version_info),
            "system": "{0}/{1}".format(platform.system(), platform.release())
        }

        # Concatenate and format the user-agent string to be passed into request headers
        ua_string = []
        for key, val in package_info.items():
            ua_string.append(val)

        return " ".join(ua_string)

    def verify_signature(self, timestamp, signature):
        # Verify the request signature of the request sent from Slack
        # Generate a new hash using the app's signing secret and request data

        if hasattr(hmac, "compare_digest"):
            req = str.encode('v0:' + str(timestamp) + ':') + self.event
            request_hash = 'v0=' + hmac.new(
                str.encode(self.signing_secret),
                req, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(request_hash, signature)
        else:
            # So, we'll compare the signatures explicitly
            req = str.encode('v0:' + str(timestamp) + ':') + self.event
            request_hash = 'v0=' + hmac.new(
                str.encode(self.signing_secret),
                req, hashlib.sha256
            ).hexdigest()

            if len(request_hash) != len(signature):
                return False
            result = 0
            if isinstance(request_hash, bytes) and isinstance(signature, bytes):
                for x, y in zip(request_hash, signature):
                    result |= x ^ y
            else:
                for x, y in zip(request_hash, signature):
                    result |= ord(x) ^ ord(y)
            return result == 0

    # send 200 as much as possible, since slack will mark any other code as failure
    def emit_error_and_respond(self, message, code=200):
        slack_exception = SlackEventsAdapterException(message)
        self.emit('error', slack_exception)
        return self.make_response("", code)

    def handle(self):
        # If a GET request is made, return 404.
        if self.request['httpMethod'] == 'GET':
            return self.make_response("These are not the slackbots you're looking for.", 404)

        if not self.event.get('api_app_id') == self.app_id:
            return self.emit_error_and_respond('App ID {} is not handled'.format(self.event.get('api_app_id', 'missing-api_app_id')))

        if self.event.get('type') == 'app_rate_limited':
            return self.emit_error_and_respond('We are being rate limited by slack for the app_id {} starting {}'.format(
                                                                        self.event.get('api_app_id', 'missing-api_app_id'),
                                                                        self.event.get('minute_rate_limited', 'missing-minute_rate_limited')))
        elif not self.event.get('type'):
            return self.emit_error_and_respond('Event type {} not supported'.format(self.event.get('type', 'missing-type')))

        # Each request comes with request timestamp and request signature
        # emit an error if the timestamp is out of range
        try:
            req_timestamp = self.request['multiValueHeaders'].get('X-Slack-Request-Timestamp', [])[0]
        except IndexError:
            return self.emit_error_and_respond('X-Slack-Request-Timestamp not found in the headers')
        else:
            if abs(time() - int(req_timestamp)) > 60 * 5:
                return self.emit_error_and_respond('Invalid request timestamp', 403)

        # Verify the request signature using the app's signing secret
        # emit an error if the signature can't be verified
        try:
            req_signature = self.request['multiValueHeaders'].get('X-Slack-Signature', [])[0]
        except IndexError:
            return self.emit_error_and_respond('X-Slack-Signature not found in the headers')
        else:
            if not self.verify_signature(req_timestamp, req_signature):
                return self.emit_error_and_respond('Invalid request signature', 403)

        # Echo the URL verification challenge code back to Slack
        if self.event.get('challenge') and self.event.get('type') == 'url_verification':
            return self.make_response(json.dumps({'challenge': self.event['challenge']}), 200)

        # Parse the Event payload and emit the event to the event listener
        if self.event.get('event') and self.event['event'].get('type') in self.accepted_event_types:
            try:
                if self.request['multiValueHeaders'].get('X-Slack-Retry-Num', [])[0]:
                    # if it's a retried event
                    self.event['event']['retry'] = True
            except IndexError:
                pass
            self.emit(self.event['event']['type'], self.event['event'])
            return self.make_response("", 200)
        else:
            return self.emit_error_and_respond('Internal event type {} not supported'.format(self.event['event'].get('type', 'missing-type')))
