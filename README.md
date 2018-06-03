# Lamia-Community

**Latest News:** We are currently pushing for a 1.00 release in September 2018. This will be our first tagged release. Until that release, use at your own risk, this is a rapidly changing project. We are calling this release 1.00 because Lamia has already been used to run live sites since 2015 and has never had significant reliability issues.

Lamia Community is a platform, built using Flask.py, for those looking for an integrated forum, blog, and status update interface without all of the assumptions made by social network platforms.

## What do I need in order to run Lamia Community?

* PostgreSQL
* Python 3.x
* Redis
* Mailgun (for now)
* Nginx (optional, but strongly recommended)

## What is Lamia Community?

Lamia is...

* A somewhat conventional forum with the unconventional feature of real time posting in threads 
* A real time "status update" system
* A somewhat conventional platform for blogging 
* A flexible and customizable user profile system

... all tied together with some added seasoning.

## Project History

In 2015, after repeated attempts, a group of hackers that had been targeting our forum finally took us offline. Our forum had been put together using a fairly vanilla copy of one of the more popular commercial forum packages. In the beginning, it had seemed like a safe bet. However, as our forum grew over time, we became intimately familiar with the frustratingly slow response times from support, an obtuse plug in interface, and expensive licensing fees.

When we were hacked, that was the last straw. We built a forum package in Python and migrated all of our content over. Over time, our initial forum evolved around a core set of features, and at some point, we realized that it made sense to open source it. Thus, Lamia was born. And... Yes. It is a headache to transform hard-coded values into configurable options. I think that this process is a great example of "learning through pain".

## Project Goals

* Remain comfortable for those that are familiar with past and present interfaces
* Keep a limited scope - the project will always consist of forum, blogs, and status updates
* Stay pretty - we think Lamia is cute, but maybe that's just us
* Keep it simple - Lamia's code is, generally, not overly complex, we would like to keep it this way
* Avoiding NiH (not invented here) as much as possible - Lamia makes intelligent use of dependencies that are license compatible

## Development Targets

Most of our current tasks are in the issue tracker, but some additional targets are here.

* Develop a full suite of tests. We're rather ashamed of the current lack of coverage. This will be fixed.
* Adding multi lingual support. This was never on the radar while Lamia was just the engine for a fan site. Now that we are working on making it more generalized, language file support is on our wish list.

## Credits and Acknowledgements 

<a href="https://freesound.org/people/FoolBoyMedia/sounds/234524/">FoolBoyMedia</a> for the notification sound. 
