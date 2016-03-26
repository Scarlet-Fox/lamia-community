from woe import app
from mako.template import Template
from mako.lookup import TemplateLookup
import requests

_mylookup = TemplateLookup(directories=[app.config['MAKO_EMAIL_TEMPLATE_DIR']])
_debug = app.config['DEBUG']
_api = app.config['MGAPI']

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
