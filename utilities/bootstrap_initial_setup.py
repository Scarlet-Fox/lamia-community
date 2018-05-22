from lamia import sqla
import lamia.sqlmodels as sqlm
from getpass import getpass
from datetime import datetime
import random
import arrow
from sqlalchemy.orm.mapper import configure_mappers
from slugify import slugify
import os.path, sys

if __name__ == "__main__":
    if os.path.exists("setup.txt"):
        print "Setup is already completed (remove setup.txt to force a database reset)."
        sys.exit()
        
    configure_mappers()
    sqla.create_all()

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

    create_setting("core.manual-validation-active", "Manual Validation is Active?", "no", "toggle", {}, "no")
    create_setting("core.lock-site", "Lock Site? (Under construction page.)", "no", "toggle", {}, "no")
    create_setting("core.swear-filter-default", "Swear filter on by default?", "no", "toggle", {}, "no")
    create_setting("core.site-name", "What's the name of this site?", "Your Site Name Here", "text", {}, "Your Site Name Here")
    create_setting("meta.author", "Site author?", "", "text", {}, "")
    create_setting("meta.description", "Site description?", "", "text", {}, "")
    create_setting("forum.allow-embed", "Allow embedded RSS content?", "no", "toggle", {}, "no")
    create_setting("twitter.twitter-consumer-key", "Twitter Consumer Key", "", "text", {}, "")
    create_setting("twitter.twitter-consumer-secret", "Twitter Consumer Secret", "", "text", {}, "")
    create_setting("twitter.twitter-access-token-key", "Twitter Access Token Key", "", "text", {}, "")
    create_setting("twitter.twitter-access-token-secret", "Twitter Access Token Secret", "", "text", {}, "")
    
    print
    print "Set a username for the first user (your admin/site owner account)"
    username = raw_input()
    password = ""
    
    print
    print "Set an email address for the first user (your admin/site owner account)"
    email = raw_input()
    
    def get_password():
        print
        print "Enter a password for this account"
        password = getpass()
        
        print
        print "Confirm your password?"
        password_confirm = getpass()
        
        if password != password_confirm:
            print
            print "Error: password did not match confirmation."
            print
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
    