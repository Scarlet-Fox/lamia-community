from lamia import app
from mako.template import Template
from mako.lookup import TemplateLookup
from urllib.parse import quote
from lamia import sqla
import lamia.sqlmodels as sqlm
import requests, arrow
from bs4 import BeautifulSoup
from lamia.utilities import get_preview_for_email
from sqlalchemy.orm.attributes import flag_modified

_mylookup = TemplateLookup(directories=[app.config['MAKO_EMAIL_TEMPLATE_DIR']])
_debug = app.config['DEBUG']
_api = app.config['MGAPI']
_mgurl = app.config['MGURL']
_base_url = app.config['BASE']

def send_notification_emails():
    __banned_users_to_check = sqla.session.query(sqlm.User).filter_by(banned=True).all()
    for _u in __banned_users_to_check:
        notifications = sqla.session.query(sqlm.Notification) \
            .filter_by(seen=False, acknowledged=False, emailed=False) \
            .filter_by(user=_u) \
            .order_by(sqla.desc(sqlm.Notification.created)).all()
        for n in notifications:
            n.emailed=True
            sqla.session.add(n)
            sqla.session.commit()

    __muted_users_to_check = sqla.session.query(sqlm.User).filter_by(emails_muted=True).all()
    for _u in __muted_users_to_check:
        notifications = sqla.session.query(sqlm.Notification) \
            .filter_by(seen=False, acknowledged=False, emailed=False) \
            .filter_by(user=_u) \
            .order_by(sqla.desc(sqlm.Notification.created)).all()
        for n in notifications:
            n.emailed=True
            sqla.session.add(n)
            sqla.session.commit()

    _users_to_check = sqla.session.query(sqlm.User).filter_by(banned=False, validated=True).all()

    notification_formats = {}
    notification_full_names = {}
    for t in sqlm.Notification.NOTIFICATION_CATEGORIES:
        notification_formats[t[0]] = t[3]
        notification_full_names[t[0]] = (t[4], t[5])

    for u in _users_to_check:
        if u.banned:
            continue

        if u.minimum_time_between_emails == None:
            u.minimum_time_between_emails = 360

        notifications = sqla.session.query(sqlm.Notification) \
            .filter_by(seen=False, acknowledged=False, emailed=False) \
            .filter_by(user=u) \
            .order_by(sqla.desc(sqlm.Notification.created)).all()
        notifications_count = len(notifications)

        try:
            if u.last_sent_notification_email > arrow.utcnow().replace(minutes=-u.minimum_time_between_emails).datetime.replace(tzinfo=None):
                continue
        except:
            pass

        _list = []
        _list_k = {}
        _list_url = {}

        _details = []
        _details_k = {}

        _summaries = []
        _summaries_k = {}
        _total = 0

        for n in notifications:
            if u.notification_preferences is None:
                u.notification_preferences = {}
                flag_modified(u, "notification_preferences")
                sqla.session.add(u)
                sqla.session.commit()

            if not u.notification_preferences.get(n.category, {"email": True}).get("email"):
                n.emailed = True
                sqla.session.add(n)
                sqla.session.commit()
                continue
            else:
                _total += 1

            if notification_formats[n.category] == "summarized":
                if n.category not in _summaries_k:
                    _summaries_k[n.category] = 1
                    _summaries.append(n.category)
                else:
                    _summaries_k[n.category] += 1

            if notification_formats[n.category] == "listed":
                if n.category not in _summaries_k:
                    _summaries_k[n.category] = 1
                    _summaries.append(n.category)
                else:
                    _summaries_k[n.category] += 1

                if _base_url+n.url in _list_url:
                    _list_url[_base_url+n.url] += 1
                    continue
                else:
                    _list_url[_base_url+n.url] = 1

                if n.category not in _list_k:
                    _list_k[n.category] = [{
                        "message": n.message,
                        "url": _base_url+n.url
                    }]
                    _list.append(n.category)
                else:
                    _list_k[n.category].append({
                        "message": n.message,
                        "url": _base_url+n.url
                    })

            if notification_formats[n.category] == "detailed":
                if n.category not in _summaries_k:
                    _summaries_k[n.category] = 1
                    _summaries.append(n.category)
                else:
                    _summaries_k[n.category] += 1

                if n.category not in _details_k:
                    _details_k[n.category] = [{
                        "url": _base_url+n.url,
                        "message": n.message,
                        "description": get_preview_for_email(n.snippet)
                    }]
                    _details.append(n.category)
                else:
                    _details_k[n.category].append({
                        "url": _base_url+n.url,
                        "message": n.message,
                        "description": get_preview_for_email(n.snippet)
                    })

        if not u.emails_muted:
            _to_email_address = False
            if _debug:
                if not u.is_admin and not u.is_allowed_during_construction:
                    continue
                else:
                    _to_email_address = u.email_address
            else:
                _to_email_address = u.email_address

            if len(_list) == 0 and len(_details) == 0 and len(_summaries) == 0:
                continue

            _template = _mylookup.get_template("notification.txt")
            _rendered = _template.render(
                _user = u,
                _base = _base_url,
                _list = _list,
                _list_k = _list_k,
                _list_url = _list_url,
                _details = _details,
                _details_k = _details_k,
                _summaries = _summaries,
                _summaries_k = _summaries_k,
                _notification_names = notification_full_names
                )

            u.last_sent_notification_email = arrow.utcnow().datetime.replace(tzinfo=None)
            sqla.session.add(u)
            sqla.session.commit()

            notifications_update = sqla.session.query(sqlm.Notification) \
                .filter_by(seen=False, acknowledged=False, emailed=False) \
                .filter_by(user=u) \
                .all()
            for n in notifications_update:
                n.emailed=True
                sqla.session.add(n)
            sqla.session.commit()
            
            if _total == 1:
                subject = "You have a notification at %s" % (app.get_site_config("core.site-name"),)
            else:
                subject = "You have %s notifications at %s" % (_total, app.get_site_config("core.site-name"))
                
            if not app.settings_file.get("lockout_on", False):
                result = requests.post(
                    _mgurl+"/messages",
                    auth=("api", _api),
                    data={"from": "%s <%s>" % (app.get_site_config("core.site-email-name"), app.get_site_config("core.site-email")),
                          "to": _to_email_address,
                          "subject": subject,
                          "text": _rendered})
            else:
                result = "LOCKDOWN ON"

            new_email_log = sqlm.EmailLog()
            new_email_log.to = u
            new_email_log.sent = arrow.utcnow().datetime.replace(tzinfo=None)
            new_email_log.subject = "You have %s notifications at %s" % (_total, app.get_site_config("core.site-name"))
            new_email_log.body = _rendered
            new_email_log.result = str(result)
            sqla.session.add(new_email_log)
            sqla.session.commit()

def send_mail_w_template(send_to, subject, template, variables):
    _to_email_addresses = []
    for user in send_to:
        if _debug:
            if not user.is_admin and not user.is_allowed_during_construction:
                continue
            else:
                _to_email_addresses.append(user.email_address)
        else:
            _to_email_addresses.append(user.email_address)
    _template = _mylookup.get_template(template)

    _rendered = _template.render(**variables)

    if not app.settings_file.get("lockout_on", False):
        response = requests.post(
            _mgurl+"/messages",
            auth=("api", _api),
            data={"from": "%s <%s>" % (app.get_site_config("core.site-email-name"), app.get_site_config("core.site-email")),
                  "to": _to_email_addresses,
                  "subject": subject,
                  "text": _template.render(**variables)})
    else:
        response = "LOCKDOWN ON"

    new_email_log = sqlm.EmailLog()
    new_email_log.to = send_to[0]
    new_email_log.sent = arrow.utcnow().datetime.replace(tzinfo=None)
    new_email_log.subject = subject
    new_email_log.body = _rendered
    new_email_log.result = str(response)
    sqla.session.add(new_email_log)
    sqla.session.commit()

    return response

def send_announcement_emails():
    for announcement in sqla.session.query(sqlm.Announcement).filter_by(draft=False).all():
        for user in sqla.session.query(sqlm.User).filter_by(banned=False, validated=True).all():
            _template = _mylookup.get_template("announcement.txt")
            _rendered = _template.render(
                message = announcement.body,
                _user = user,
                _base = _base_url
            )

            response = 200

            if not user.emails_muted:
                if not app.settings_file.get("lockout_on", False):
                    result = requests.post(
                        _mgurl+"/messages",
                        auth=("api", _api),
                        data={"from": "%s <%s>" % (app.get_site_config("core.site-email-name"), app.get_site_config("core.site-email")),
                              "to": user.email_address,
                              "subject": announcement.subject,
                              "text": _rendered})
                else:
                    result = "LOCKDOWN ON"

                new_email_log = sqlm.EmailLog()
                new_email_log.to = user
                new_email_log.sent = arrow.utcnow().datetime.replace(tzinfo=None)
                new_email_log.subject = announcement.subject
                new_email_log.body = _rendered
                new_email_log.result = str(result)
                sqla.session.add(new_email_log)
                sqla.session.commit()

        announcement.sent = arrow.utcnow().datetime.replace(tzinfo=None)
        sqla.session.add(announcement)
        sqla.session.commit()
