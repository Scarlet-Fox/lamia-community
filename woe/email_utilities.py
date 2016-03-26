from woe import app
from mako.template import Template
from mako.lookup import TemplateLookup
from woe import sqla
import woe.sqlmodels as sqlm
import requests, arrow

_mylookup = TemplateLookup(directories=[app.config['MAKO_EMAIL_TEMPLATE_DIR']])
_debug = app.config['DEBUG']
_api = app.config['MGAPI']

def send_notification_emails():
    _users_to_check = sqla.session.query(sqlm.User) \
        .filter(
            sqla.or_(
                sqlm.User.last_sent_notification_email == None,
                sqlm.User.last_sent_notification_email < arrow.utcnow().replace(hours=-5).datetime.replace(tzinfo=None)
            )
        )

    for u in _users_to_check:
        notifications = sqla.session.query(sqlm.Notification).filter_by(seen=False, acknowledged=False, emailed=False).all()

        if u.login_name == "scarlet":
            print u.login_name
            print [i.category for i in notifications]


def send_mail_w_template(send_to, subject, template, variables):
    _to_email_addresses = []
    for user in send_to:
        if _debug:
            if not user.is_admin and not user.is_allowed_during_construction:
                continue
            else:
                _to_email_addresses.append(user.email_address)
    _template = _mylookup.get_template(template)

    # print _to_email_addresses
    # print template
    # print variables
    # print _template.render(**variables)

    return requests.post(
        "https://api.mailgun.net/v3/scarletsweb.moe/messages",
        auth=("api", _api),
        data={"from": "Scarlet's Web <sally@scarletsweb.moe>",
              "to": _to_email_addresses,
              "subject": subject,
              "text": _template.render(**variables)})
