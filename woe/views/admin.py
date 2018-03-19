from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose
from flask_admin.contrib.sqla import ModelView
from woe import sqla
import woe.sqlmodels as sqlm
from jinja2 import Markup
import arrow

class AuthAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_mod and not current_user.is_admin:
            return redirect("/")
            
        all_active_reports = sqlm.Report.query.filter(sqlm.Report.status.in_(["open", "feedback", "waiting"])).count()
        recent_infractions = sqlm.Infraction.query.filter(sqlm.Infraction.created > arrow.utcnow().replace(days=-7).datetime).count()
        active_bans = sqlm.Ban.query.filter_by(forever=False).filter(sqlm.Ban.expires > arrow.utcnow().datetime).count()
            
        if current_user.is_admin:
            my_area_reports = all_active_reports
        else:
            my_areas = []
        
            if current_user.can_mod_blogs:
                my_areas.append("blogentry")
                my_areas.append("blogcomment")
        
            if current_user.can_mod_user_profiles:
                my_areas.append("user")
        
            if current_user.can_mod_status_updates:
                my_areas.append("status")
                
            my_area_reports = 0
        
        return self.render('admin/index.html', 
                all_active_reports=all_active_reports,
                recent_infractions=recent_infractions,
                active_bans=active_bans,
                my_area_reports=my_area_reports
            )

admin = admin.Admin(app, index_view=AuthAdminIndexView(), name="Staff CP")


