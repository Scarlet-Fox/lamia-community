from lamia import sqla
import lamia.sqlmodels as sqlm

def create_setting(hierarchy, key, default_value, option_type, meta, default):
    try:
        _setting = sqlm.SiteConfiguration(
                hierarchy=hierarchy,
                key=key,
                value=default_value,
                option_type=option_type,
                meta=meta,
                default=default
            )
    
        sqla.session.add(_setting)
        sqla.session.commit()
    except:
        sqla.session.rollback()

create_setting("core.manual-validation-active", "Manual Validation is Active?", "no", "toggle", {}, "no")
create_setting("core.lock-site", "Lock Site? (Under construction page.)", "no", "toggle", {}, "no")
create_setting("core.swear-filter-default", "Swear filter on by default?", "yes", "toggle", {}, "yes")
create_setting("core.site-name", "What's the name of this site?", "Your Site Name Here", "text", {}, "Your Site Name Here")
create_setting("twitter.twitter-consumer-key", "Twitter Consumer Key", "", "text", {}, "")
create_setting("twitter.twitter-consumer-secret", "Twitter Consumer Secret", "", "text", {}, "")
create_setting("twitter.twitter-access-token-key", "Twitter Access Token Key", "", "text", {}, "")
create_setting("twitter.twitter-access-token-secret", "Twitter Access Token Secret", "", "text", {}, "")
