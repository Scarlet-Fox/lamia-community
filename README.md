# Lamia-Community

**Latest News:** This is dead. Forums are dead. Do not use forums. Do not use this. This is here only because it was once here and fuck, it might as well stay here since it was open source. Consider it a monument to obsolescence and my sins, which are so numerous that you can't even begin to imagine them all.

No seriously, don't use this, it's dead and I can't be assed to maintain it. This is serious because some of the dependencies have security vulnerabilities that have come up since this died. I haven't done anything about that and I'm not going to, because I need to move on. You should too. Life is better that way.

Thank you for coming to my ted talk. Please like and subscribe.

OLD STUFF FROM WHEN I WAS ACTUALLY MAINTAINING THIS CONTINUES BELOW. IT IS OLD.

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

## How to get started?

I'm going to assume that you're using Linux, because that makes life easier. If you aren't then you should send a PM to Zephyr on the Lamia Community website, and we will try to help you get going.

Keep in mind, you should not base your community on Lamia until 1.00 is released. I am only providing these instructions for the purpose of helping developers that are hoping to contribute to Lamia's development (or just curious and wanting to poke holes into things). 

Seriously. We will not make any migration scripts for upgrading versions until 1.00 is released, so *do not use Lamia in production until that time unless you are Zephyr or you really know what tf you're doing*. You have been warned. :3

1. Install the latest version of Python 3.x that you can get your hands on
2. Install libxml-dev, python3-dev, redis-server, postgresql-server, imagemagick, and libncurses5-dev
3. Get everything setup and running (you need to have postgres running and redis (make sure you have a db setup!))
4. Get a Mailgun account (I'm sorry, this requirement will be removed later)
5. Copy the config.json.example file and modify it with your own settings
6. In the lamia root, run the following command 'python utilities/bootstrap_initial_setup.py'
7. Answer the questions
8. Run the following comment 'python manage.py runserver'
9. For real time notifications, install nodejs and npm
10. From the lamia root, run 'npm install expressjs socket.io coffee-script'
11. Run './node_modules/coffeescript/bin/coffee ./listener.coffee'

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
