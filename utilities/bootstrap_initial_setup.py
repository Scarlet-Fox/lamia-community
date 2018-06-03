import os.path, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lamia import sqla
import lamia.sqlmodels as sqlm
from getpass import getpass
from datetime import datetime
import random
import arrow
from sqlalchemy.orm.mapper import configure_mappers
from slugify import slugify

def create_setting(hierarchy, key, default_value, option_type, local_meta, default):
    try:
        _setting = sqlm.SiteConfiguration(
                hierarchy=hierarchy,
                key=key,
                value=default_value,
                option_type=option_type,
                local_meta=local_meta,
                default=default
            )

        sqla.session.add(_setting)
        sqla.session.commit()
    except:
        sqla.session.rollback()

def add_email_template(name, template):
    try:
        _template = sqlm.EmailTemplate(
            name = name,
            template = template
        )
        
        sqla.session.add(_template)
        sqla.session.commit()
    except:
        sqla.session.rollback()

if __name__ == "__main__":
    if os.path.exists("setup.txt"):
        print("Setup is already completed (remove setup.txt to force a database reset).")
        sys.exit()
        
    configure_mappers()
    sqla.create_all()

    create_setting("core.manual-validation-active", "Manual Validation is Active?", "no", "toggle", {}, "no")
    create_setting("core.lock-site", "Lock Site? (Under construction page.)", "no", "toggle", {}, "no")
    create_setting("core.swear-filter-default", "Swear filter on by default?", "no", "toggle", {}, "no")
    create_setting("core.site-name", "What's the name of this site?", "Your Site Name Here", "text", {}, "Your Site Name Here")
    create_setting("core.site-email", "What's this site's email address?", "", "text", {}, "")
    create_setting("core.site-email-name", "Who (or what) is sending your emails?", "", "text", {}, "")
    create_setting("meta.author", "Site author?", "", "text", {}, "")
    create_setting("meta.description", "Site description?", "", "text", {}, "")
    create_setting("forum.allow-embed", "Allow embedded RSS content?", "no", "toggle", {}, "no")
    create_setting("twitter.twitter-consumer-key", "Twitter Consumer Key", "", "text", {}, "")
    create_setting("twitter.twitter-consumer-secret", "Twitter Consumer Secret", "", "text", {}, "")
    create_setting("twitter.twitter-access-token-key", "Twitter Access Token Key", "", "text", {}, "")
    create_setting("twitter.twitter-access-token-secret", "Twitter Access Token Secret", "", "text", {}, "")
    
    add_email_template(
        "announcement",
"""Hello ${_user.display_name},

${message}

To unsubscribe from all future messages, go to this page - ${_base}/member/${_user.id}/${_user.email_address}/unsubscribe"""
    )
    
    add_email_template(
        "manual_validation_welcome",
"""Hello ${_user.display_name},

Welcome to our community! It is great to have you as a member of our community!

Your account has been manually validated by our staff. This means that you are now ready to sign in!

${address}

We look forward to seeing you around. :)

Take care!
- The Administration"""
    )
    
    add_email_template(
        "notification",
"""Hello ${_user.display_name},

You have unread notifications,

% for category in _summaries:
    % if _summaries_k[category] == 1:
- You have received 1 ${_notification_names[category][0].lower()} notification.
    % else:
- You have received ${_summaries_k[category]} ${_notification_names[category][0].lower()} notifications.
    % endif
% endfor
% if len(_summaries) > 0:

You can find more details about these summarized items on your dashboard, when you login.
% endif

% for category in _list:
${_notification_names[category][0].capitalize()} Notification(s)
===================
    % for item in _list_k[category]:
        % if _list_url[item["url"]] == 1:
- ${item["message"]} 
 ${item["url"]}
        % else:
- ${item["message"]} with ${_list_url[item["url"]]-1} other notification(s) 
 ${item["url"]}
        % endif
    % endfor
% if category != _list[-1]:

% endif
% endfor

% for category in _details:
${_notification_names[category][0].capitalize()} Notification(s)
===================
    % for item in _details_k[category]:
- ${item["message"]} 
(${item["url"]})
"${item["description"]}"

    % endfor
% if category != _details[-1]:
% endif
% endfor

-------------------
To change your notification preferences, go to the settings area on your profile page - ${_base}/member/${_user.get_url_safe_login_name()}/change-settings

To unsubscribe from all future messages from our community, go to this page - ${_base}/member/${_user.id}/${_user.email_address}/unsubscribe"""
    )
    
    add_email_template(
        "password_reset",
"""Hello ${display_name},

Either you or someone pretending to be you has requested a password reset at our community. 

If it was you, then you can use this address to set your new password:

${address}

If you did not request this, then you should let us know by replying to this email.

- The Administration"""
    )
    
    add_email_template(
        "pending_validation",
"""Hello ${_user.display_name},

Thank you for registering at our community! Please be patient while our administrators review your account application. We review all accounts manually to protect the community from spammers, trolls and other troublemakers.

This process usually doesn't take very long. However, on occasion, there may be a slight delay. You will receive an email notification when your account has been validated. :)

To unsubscribe from all future messages from us, go to this page - ${_base}/member/${_user.id}/${_user.email_address}/unsubscribe - after your account has been validated.

- The Administration"""
    )
    
    add_email_template(
        "welcome",
"""Hello ${_user.display_name},

Welcome! It is great to have you as a member of our community!

Please click the following link to confirm your shiny new member account:

${address}

We look forward to seeing you around. :)

Take care!
- The Administration"""
    )
    
    print()
    print("Set a username for the first user (your admin/site owner account)")
    username = input()
    password = ""
    
    print()
    print("Set an email address for the first user (your admin/site owner account)")
    email = input()
    
    def get_password():
        print()
        print("Enter a password for this account")
        password = getpass()
        
        print()
        print("Confirm your password?")
        password_confirm = getpass()
        
        if password != password_confirm:
            print()
            print("Error: password did not match confirmation.")
            print()
            return get_password()
        
        return password
    
    password = get_password()
            
    new_user = sqlm.User(
        login_name = username.strip().lower(),
        my_url = slugify(username).strip().lower(),
        display_name = username,
        email_address = email
    )
    new_user.set_password(password.strip())
    new_user.joined = arrow.utcnow().datetime
    new_user.over_thirteeen = True
    new_user.validated = True
    new_user.is_admin = True
    new_user.how_did_you_find_us = "I am the creator."
    sqla.session.add(new_user)
    sqla.session.commit()
    
    setup_file = open("setup.txt", "w")
    setup_file.write("Completed")
    setup_file.close()
    