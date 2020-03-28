Slack Events API adapter for AWS Lambda
=======================================

The Slack Events Adapter is a Python-based solution to receive and parse events
from Slack’s Events API through AWS Lambda via ALB. This library uses an event emitter framework to allow
you to easily process Lambda Slack events from AWS ALB (Application load balancer) by simply attaching functions
to event listeners.

This adapter enhances and simplifies Slack's Events API by incorporating useful best practices, patterns, and opportunities to abstract out common tasks.

💡  Slack has written a `blog post which explains how`_ the Events API can help you, why we built these tools, and how you can use them to build production-ready Slack apps.

.. _blog post which explains how: https://medium.com/@SlackAPI/enhancing-slacks-events-api-7535827829ab


🤖  Installation
----------------

.. code:: shell

  pip install slacklambdaevents

🤖  App Setup
--------------------

Before you can use the `Events API`_ you must
`create a Slack App`_, and turn on
`Event Subscriptions`_.

💡  When you add the Request URL to your app's Event Subscription settings,
Slack will send a request containing a `challenge` code to verify that your
server is alive. This package handles that URL Verification event for you, so
all you need to do is plug the adapter in the lambda function and start using it.

✅  Once you have your `Request URL` verified, your app is ready to start
receiving Events.

🔑  Your server will begin receiving Events from Slack's Events API as soon as a
user has authorized your app.

🤖  Development workflow:
===========================

(1) Create a Slack app on https://api.slack.com/apps
(2) Add a `bot user` for your app
(3) Start the example app on your **Request URL** endpoint
(4) Create Lambda and ALB endpoint and copy the **HTTPS** URL
(5) Add your **Request URL** and subscribe your app to events
(6) Go to your ALB URL and auth your app

**🎉 Once your app has been authorized, you will begin receiving Slack Events**


🤖  Usage
----------
  **⚠️  Keep your app's credentials safe!**

  - For development, keep them in virtualenv variables.

  - For production, use a secure data store.

  - Never post your app's credentials to github.

.. code:: python

  SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

Create a Slack Event Adapter for receiving actions via the Events API
-----------------------------------------------------------------------

.. code:: python

  from slacklambdaevents import SlackEventsAdapter


  slack_events_adapter = SlackEventsAdapter(lamdbaEvent, SLACK_SIGNING_SECRET)


  # Create an event listener for "reaction_added" events and print the emoji name
  @slack_events_adapter.on("reaction_added")
  def reaction_added(event_data):
    emoji = event_data["event"]["reaction"]
    print(emoji)


For a comprehensive list of available Slack `Events` and more information on
`Scopes`, see https://api.slack.com/events-api

🤖  Example event listeners
-----------------------------

See `example.py`_ for usage examples. This example also utilizes the
SlackClient Web API client.

.. _example.py: /example/

🤔  Support
-----------

.. _Events API: https://api.slack.com/events-api
.. _create a Slack App: https://api.slack.com/apps/new
.. _Event Subscriptions: https://api.slack.com/events-api#subscriptions
.. _Slack Community: http://slackcommunity.com/
.. _create an Issue: https://github.com/slackapi/python-slack-events-api/issues/new
