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
            my_area_reports = sqlm.Report.query.filter(
                    sqlm.Report.status.in_(["open", "feedback", "waiting"]),
                    sqlm.Report.report_area.in_(current_user.get_modded_areas())
                ).count()
        
        return self.render('admin/index.html', 
                all_active_reports=all_active_reports,
                recent_infractions=recent_infractions,
                active_bans=active_bans,
                my_area_reports=my_area_reports
            )
admin = admin.Admin(app, index_view=AuthAdminIndexView(), name="Staff CP")

class MyReportView(ModelView):
    can_view_details = True
    can_edit = False
    can_create = False
    can_delete = False
    column_list = ["report_author", "content_author", "report_area", "status"]
    column_labels = dict(content_author="The Defendent", report_author="The Accuser")
    
    # def _user_formatter(view, context, model, name):
    #         if model.url:
    #            markupstring = "<a href='%s'>%s</a>" % (model.url, model.urltitle)
    #            return Markup(markupstring)
    #         else:
    #            return ""
    #
    #     column_formatters = {
    #         'url': _user_formatter
    #     }    
    
    def get_query(self):
        if current_user.is_admin:
            return self.session.query(self.model)
        else:
            return self.session.query(self.model).filter(
                                self.model.status.in_(["open", "feedback", "waiting"]),
                                self.model.report_area.in_(current_user.get_modded_areas())
                            )
    
    def get_query_count(self):
        return self.session.query(func.count('*')).select_from(self.model).filter(
                            self.model.status.in_(["open", "feedback", "waiting"]),
                            self.model.report_area.in_(current_user.get_modded_areas())
                        )
        
    
admin.add_view(MyReportView(sqlm.Report, sqla.session, name='My Reports', category="Moderation"))


# TODO - Add "user" parser which would load avatars and such
# TODO - Add "slug formatter" which would humanize slugs
# TODO - Add indicators for report statuses

# TODO Moderation
# TODO Add my reports list view
# TODO Add global reports list view
# TODO Add completed reports list view
# TODO Add comment loading ajax view
# TODO Add new comment ajax view
# TODO Add individual report custom view
# TODO Add active infraction list view
# TODO Add most wanted listing
# TODO Add listing of users by current infr
# TODO Add ajax view for creating infraction
# TODO Add view for active bans
# TODO Add ajax view for modifying a ban
# TODO Add chart to the front showing reports vs infractions
# TODO Show recent moderation alerts
# TODO Log all moderation actions
# TODO Verify that all front end moderation actions are working
# TODO Add mod actions that are missing
# TODO Add status reply mod actions
# TODO Add code for jump to status reply
# TODO Write burning board status import script