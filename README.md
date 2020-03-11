# Sentry Pagerduty

Plugin for Sentry which allows sending notification via  [Pagerduty](https://www.pagerduty.com/) service.

## Installation

1.  Install this package
	`pip install https://github.com/kumarappan-arumugam/sentry-pagerduty/archive/master.zip`
2.  Restart your Sentry service.
3.  Go to your Sentry web interface. Open  organization `Settings`  page.
4.  On  `Integrations`, find  `Pagerduty`  plugin and install it.
5.  Configure plugin on  `Configure plugin`  page.
    See  [Pagerduty's documentation](https://www.pagerduty.com/docs/guides/sentry-integration-guide/)  to know how to create  `API key`.
    *Note*: Documentation for sentry configuration on pagerduty page is for [legacy integration](https://help.sentry.io/hc/en-us/articles/360003063454-What-are-Global-versus-Legacy-integrations).
6.  Done!

## FAQ

1. Do incidents that are triggered in PagerDuty create a new Issue in Sentry?

	No, the integration only sends information from Sentry to PagerDuty. This is not a 2-way integration.

2. If an incident is resolved in PagerDuty, is the issue resolved in Sentry, or vice versa?

	No, the current integration only sends the trigger information from Sentry to PagerDuty.

3. Can I setup multiple Sentry Projects be tied to the same PagerDuty service?

	Yes! When you are creating the new Project in Sentry, simply use the same Integration Key as the PagerDuty service where you wish to have the alerts trigger.

4. Can I setup multiple pagerduty services be tied to the same sentry project?

	Yes! Since this uses the new Pagerduty Events API, you can simply use the different service names to route to different services where you wish to have the alerts trigger.

## Setup

* [Step 1](_images/Step-1.png?raw=true "Step 1")
* [Step 2](_images/Step-2.png?raw=true "Step 2")
* [Step 3](_images/Step-3.png?raw=true "Step 3")
* [Step 4](_images/Step-4.png?raw=true "Step 4")
* [Step 5](_images/Step-5.png?raw=true "Step 5")
* [Step 6](_images/Step-6.png?raw=true "Step 6")
* [Step 7](_images/Step-7.png?raw=true "Step 7")
