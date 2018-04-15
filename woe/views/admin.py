from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from wtforms import BooleanField, StringField, TextAreaField, PasswordField, validators, SelectField, HiddenField, IntegerField, DateField
from flask_login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose, BaseView, form
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from woe import sqla
import woe.sqlmodels as sqlm
from jinja2 import Markup
import arrow
from woe.utilities import humanize_time, ForumHTMLCleaner
from woe.parsers import ForumPostParser
from flask_admin.contrib.sqla.form import AdminModelConverter
import os, os.path
from sqlalchemy import or_
from flask_admin._compat import as_unicode, string_types
from flask_admin.model.ajax import AjaxModelLoader, DEFAULT_PAGE_SIZE
_base_url = app.config['BASE']

###################################################################################################
# Special classes
###################################################################################################

class StartsWithQueryAjaxModelLoader(QueryAjaxModelLoader):
    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.session.query(self.model)

        filters = (field.startswith(u'%s' % term) for field in self._cached_fields)
        query = query.filter(or_(*filters))

        return query.offset(offset).limit(limit).all()

###################################################################################################
# Base admin view (index)
###################################################################################################

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
                    sqlm.Report.report_area.in_(current_user.get_modded_areas)
                ).count()
        
        return self.render('admin/index.html', 
                all_active_reports=all_active_reports,
                recent_infractions=recent_infractions,
                active_bans=active_bans,
                my_area_reports=my_area_reports
            )
admin = admin.Admin(app, index_view=AuthAdminIndexView(), name="Staff CP")

###################################################################################################
# Column formatters
###################################################################################################

def _user_list_formatter(view, context, model, name):
    user = getattr(model, name)
    if not user:
        return ""
        
    prettified_user = \
    u"""<div><a href="/member/%s"><img src="%s" width="%spx" height="%spx" class="avatar-mini" style="margin-right: 15px;"/></a><a class="hover_user" href="/member/%s">%s</a></div>""" \
        % (unicode(user.my_url),
        user.get_avatar_url("40"),
        user.avatar_40_x,
        user.avatar_40_y,
        unicode(user.my_url),
        unicode(user.display_name))
        
    return Markup(prettified_user)

def _user_formatter(view, context, model, name):
    user = model
    if not user:
        return ""
        
    prettified_user = \
    u"""<div><a href="/member/%s"><img src="%s" width="%spx" height="%spx" class="avatar-mini" style="margin-right: 15px;"/></a><a class="hover_user" href="/member/%s">%s</a></div>""" \
        % (unicode(user.my_url),
        user.get_avatar_url("40"),
        user.avatar_40_x,
        user.avatar_40_y,
        unicode(user.my_url),
        unicode(user.display_name))
        
    return Markup(prettified_user)

def _unslugify_formatter(view, context, model, name):
    field = getattr(model, name)
    return field.replace("-", " ").title()

def _unslugify_list_formatter(view, context, model, name):
    field = getattr(model, name)
    return ", ".join([x.replace("-", " ").title() for x in field])

def _report_status_formatter(view, context, model, name):
    status = getattr(model, name)
    _template = "<div style=\"font-size: 1.25em; font-weight: bold; color: %s;\"><i class=\"%s\"></i>&nbsp;%s</div>"
    formats = {
        "ignored": ("black", "far fa-times-circle","Ignored",),
        "open": ("#800000", "far fa-circle","Open",),
        "feedback": ("#804d00", "far fa-question-circle","Feedback Requested",),
        "waiting": ("#000080", "far fa-clock","Waiting",),
        "actiontaken": ("#008000", "far fa-check-circle","Done",),
        "working": ("#660080", "far fa-play-circle","Working",)
    }
    return Markup(_template % formats[status])
    
def _age_from_time_formatter(view, context, model, name):
    time = arrow.get(getattr(model, name))
    now = arrow.utcnow()
    
    age = (now - time).days
    if age < 1:
        return "Today"
        
    return "%s days old" % (age, )

def _null_number_formatter(view, context, model, name):
    number = getattr(model, name)
    if not number:
        return 0
    else:
        return number
        
def _fancy_time_formatter(view, context, model, name):
    time = getattr(model, name)
    return humanize_time(time)

def _fancy_time_formatter_for_expirations(view, context, model, name):
    time = getattr(model, name)
    if time:
        return humanize_time(time)
    else:
        return "Never"

def _content_formatter(view, context, model, name):
    _html = getattr(model, name)
    
    clean_html_parser = ForumPostParser()
    return Markup(clean_html_parser.parse(_html).replace("parsed\"", "parsed\" style=\"max-height: 300px; overflow-y: scroll;\""))

def _smiley_image_formatter(view, context, model, name):
    _filename = getattr(model, name)
    return Markup("<img style=\"max-height: 50px;\" src=\"/static/smilies/%s\">" % _filename)

def _attachment_image_formatter(view, context, model, name):
    _filename = getattr(model, name)
    return Markup("<img style=\"max-height: 50px;\" src=\"/static/uploads/%s\">" % _filename)
    
def _file_size_formatter(view, context, model, name):
    _size = getattr(model, name)
    return "{:.1f} MB".format(float(_size)/1024/1024)

def _category_name_formatter(view, context, model, name):
    _name = getattr(model, name)
    return "<strong>%s</strong>" % (_name,)
    
def _role_formatter(view, context, model, name):
    _pre_html = model.pre_html if model.pre_html else ""
    _role = model.role if model.role else ""
    _post_html = model.post_html if model.post_html else ""
    return Markup("%s%s%s" % (_pre_html, _role, _post_html))
    
###################################################################################################
# Moderation views : reporting
###################################################################################################

class MyReportView(ModelView):
    can_view_details = True
    can_edit = False
    can_create = False
    can_delete = False
    column_default_sort = ('created', False)
    details_template = 'admin/model/report_details.html'
    column_list = ["status", "report_area", "created", "report_comment_count", "report_last_updated", "content_author"]
    column_details_list = [
        "report_area", "created", "status", "report_author", "content_author",
        "report_message", "reported_content_html"
    ]
    column_labels = dict(content_author="Defendent", report_author="Accuser", created="Report Age",
        report_comment_count="Comments", report_last_updated="Last Updated", reported_content_html="Reported Content")
    # TODO - unhardcode these urls
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js", 
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
    
    column_formatters = {
        'report_author': _user_list_formatter,
        'content_author': _user_list_formatter,
        'report_area': _unslugify_formatter,
        'status': _report_status_formatter,
        'created': _age_from_time_formatter,
        'report_comment_count': _null_number_formatter,
        'report_last_updated': _fancy_time_formatter,
        'reported_content_html': _content_formatter
    }
    
    def is_accessible(self):
        return current_user.is_admin or current_user.is_mod
    
    def get_query(self):
        if current_user.is_admin:
            return self.session.query(self.model).filter(
                                self.model.status.in_(["open", "feedback", "waiting", "working"]),
                            )
        else:
            return self.session.query(self.model).filter(
                                self.model.status.in_(["open", "feedback", "waiting", "working"]),
                                self.model.report_area.in_(current_user.get_modded_areas)
                            )
    
    def get_count_query(self):
        if current_user.is_admin:
            return self.session.query(sqla.func.count('*')).select_from(self.model).filter(
                                self.model.status.in_(["open", "feedback", "waiting", "working"]),
                            )
        else:
            return self.session.query(sqla.func.count('*')).select_from(self.model).filter(
                                self.model.status.in_(["open", "feedback", "waiting", "working"]),
                                self.model.report_area.in_(current_user.get_modded_areas)
                            )
                            
class ReportArchiveView(MyReportView):  
    column_default_sort = ('report_last_updated', False)
      
    def get_query(self):
        if current_user.is_admin:
            return self.session.query(self.model).filter(
                                sqla.not_(self.model.status.in_(["open", "feedback", "waiting", "working"])),
                            )
        else:
            return self.session.query(self.model).filter(
                                sqla.not_(self.model.status.in_(["open", "feedback", "waiting", "working"])),
                                self.model.report_area.in_(current_user.get_modded_areas)
                            )
    
    def get_count_query(self):
        if current_user.is_admin:
            return self.session.query(sqla.func.count('*')).select_from(self.model).filter(
                                sqla.not_(self.model.status.in_(["open", "feedback", "waiting", "working"])),
                            )
        else:
            return self.session.query(sqla.func.count('*')).select_from(self.model).filter(
                                sqla.not_(self.model.status.in_(["open", "feedback", "waiting", "working"])),
                                self.model.report_area.in_(current_user.get_modded_areas)
                            )
                            
class AllOpenReportsView(MyReportView):
    def get_query(self):
        return self.session.query(self.model).filter(
                            self.model.status.in_(["open", "feedback", "waiting", "working"]),
                        )
    
    def get_count_query(self):
        return self.session.query(sqla.func.count('*')).select_from(self.model).filter(
                            self.model.status.in_(["open", "feedback", "waiting", "working"]),
                        )
             
class ReportActionView(BaseView):
    def is_visible(self):
        return False
        
    @expose('/')
    def index(self):
        return ""
        
    def is_accessible(self):
        return current_user.is_admin or current_user.is_mod
        
    @expose('/new-comment/<idx>', methods=('POST', ))
    def add_comment(self, idx):
        _model = sqlm.Report.query.filter_by(id=idx)[0]
        
        if not current_user.is_admin and not current_user.is_mod:
            return abort(404)
        
        request_json = request.get_json(force=True)

        if request_json.get("text", "").strip() == "":
            return app.jsonify(no_content=True)
        
        cleaner = ForumHTMLCleaner()
        try:
            post_html = cleaner.clean(request_json.get("post", ""))
        except:
            return abort(500)
        
        _comment = sqlm.ReportComment(
                created = arrow.utcnow().datetime.replace(tzinfo=None),
                comment = post_html,
                is_status_change = False,
                author = current_user,
                report = _model
            )
        
        _model.report_last_updated = arrow.utcnow().datetime.replace(tzinfo=None)
        _model.report_comment_count = sqla.session.query(sqla.func.count('*')).select_from(sqlm.ReportComment) \
                .filter_by(report=_model, is_status_change=False)
        
        sqla.session.add(_comment)
        sqla.session.add(_model)
        sqla.session.commit()
        
        return app.jsonify(success=True)
        
    @expose('/mark-<status>/<idx>', methods=('POST', ))
    def mark_done(self, idx, status):
        _model = sqlm.Report.query.filter_by(id=idx)[0]
        
        if not current_user.is_admin and not _model.report_area in current_user.get_modded_areas:
            return abort(404)
            
        if not status in [sc[0] for sc in sqlm.Report.STATUS_CHOICES]:
            return abort(404)
        
        _fancy_status_names = dict((x, y) for x, y in sqlm.Report.STATUS_CHOICES)
        
        old_status = _model.status
        _model.report_last_updated = arrow.utcnow().datetime.replace(tzinfo=None)
        _model.status = status
        _new_status = _fancy_status_names[status]
        _old_status = _fancy_status_names[old_status]
        
        if status in ["actiontaken", "ignored"] and not old_status in ["actiontaken", "ignored"]:
            _model.resolved = arrow.utcnow().datetime.replace(tzinfo=None)
            _model.mark_as_resolved_by = current_user
        
        sqla.session.add(_model)
        sqla.session.commit()
        
        _comment = sqlm.ReportComment(
                created = arrow.utcnow().datetime.replace(tzinfo=None),
                comment = "changed status from \"%s\" to \"%s\"" % (_old_status, _new_status),
                is_status_change = True,
                author = current_user,
                report = _model
            )
        
        sqla.session.add(_comment)
        sqla.session.commit()
        
        return "ok"
    
admin.add_view(ReportActionView(endpoint='report', name="Report Utilities"))
admin.add_view(MyReportView(sqlm.Report, sqla.session, name='Open in My Area', category="Reports", endpoint='my-reports'))
admin.add_view(AllOpenReportsView(sqlm.Report, sqla.session, name='All Open Reports', category="Reports", endpoint='all-reports'))
admin.add_view(ReportArchiveView(sqlm.Report, sqla.session, name='Archived Reports', category="Reports", endpoint='report-archive'))

###################################################################################################
# Moderation views : infractions
###################################################################################################

class InfractionView(ModelView):
    can_view_details = True
    can_delete = False
    can_create = False
    column_default_sort = ('created', True)
    column_list = ["title", "author", "recipient", "points", "created", "expires"]
    
    form_ajax_refs = {
        'author': StartsWithQueryAjaxModelLoader('author', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
        'recipient': StartsWithQueryAjaxModelLoader('recipient', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
        'deleted_by': StartsWithQueryAjaxModelLoader('deleted_by', sqla.session, sqlm.User, fields=['display_name',], page_size=10)
    }
    column_formatters = {
            'author': _user_list_formatter,
            'recipient': _user_list_formatter,
            'created': _age_from_time_formatter,
            'expires': _fancy_time_formatter_for_expirations
        }
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    def is_accessible(self):
        if not current_user.is_admin:
            self.can_edit = False
            self.can_create = False
            
        return current_user.is_admin or current_user.is_mod

class MostWanted(ModelView):
    can_view_details = True
    can_delete = False
    can_edit = False
    can_create = False
    column_default_sort = ('lifetime_infraction_points', True)
    column_list = ["display_name", "lifetime_infraction_points", "banned"]
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    def get_query(self):
        return self.session.query(self.model).filter_by(banned=False) \
            .filter(self.model.lifetime_infraction_points > 0)
    
    def get_count_query(self):
        return self.session.query(sqla.func.count('*')).select_from(self.model).filter_by(banned=False) \
            .filter(self.model.lifetime_infraction_points > 0)
        
    def is_accessible(self):
        return current_user.is_admin or current_user.is_mod
        
class CurrentInfractions(MostWanted):
    column_default_sort = ('active_infraction_points', True)
    column_list = ["display_name", "active_infraction_points", "banned"]
        
    def is_accessible(self):
        return current_user.is_admin or current_user.is_mod
        
    def get_query(self):
        return self.session.query(self.model).filter_by(banned=False) \
            .filter(self.model.active_infraction_points > 0)
    
    def get_count_query(self):
        return self.session.query(sqla.func.count('*')).select_from(self.model).filter_by(banned=False) \
            .filter(self.model.active_infraction_points > 0)

class InfractionPresetView(ModelView):
    column_list = ["title", "points"]
        
    def is_accessible(self):
        return current_user.is_admin
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]

admin.add_view(InfractionView(sqlm.Infraction, sqla.session, name='Infraction Log', category="Infractions", endpoint='infractions'))
admin.add_view(CurrentInfractions(sqlm.User, sqla.session, name='Active Infractions', category="Infractions", endpoint='active-infractions'))
admin.add_view(MostWanted(sqlm.User, sqla.session, name='Most Infracted', category="Infractions", endpoint='most-infractions'))
admin.add_view(InfractionPresetView(sqlm.InfractionPreset, sqla.session, name='Infraction Presets', category="Infractions", endpoint='infraction-presets'))

###################################################################################################
# Moderation views : bans
###################################################################################################

class BanView(ModelView):
    can_view_details = True
    can_delete = False
    column_default_sort = ('created', True)
    column_list = ["recipient", "explanation", "created", "expires"]
    
    form_ajax_refs = {
        'recipient': StartsWithQueryAjaxModelLoader('recipient', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
    }
    column_formatters = {
            'recipient': _user_list_formatter,
            'created': _age_from_time_formatter,
            'expires': _fancy_time_formatter_for_expirations
        }
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    def is_accessible(self):
        if not current_user.is_admin:
            self.can_edit = False
            self.can_create = False
            
        return current_user.is_admin or current_user.is_mod

admin.add_view(BanView(sqlm.Ban, sqla.session, name='Ban Log', category="Bans", endpoint='recent-bans'))

###################################################################################################
# Administrative views : site settings, options, and config
###################################################################################################

class ConfigurationView(ModelView):
    can_delete = False
    edit_modal = True
    can_create = False
    column_list = ["hierarchy","key","value","default"]
    form_excluded_columns = ["hierarchy","key","meta","option_type","default"]
    column_default_sort = ('hierarchy', False)
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js", 
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    def edit_form(self, obj=None):
        if obj.option_type == "toggle":
            self.form_choices = {
                    "value": [ ('yes', 'Yes'), ('no', 'No')]
                }
        self._edit_form_class = self.get_edit_form()
        request._key = obj.key
        return super(ConfigurationView, self).edit_form(obj)
        
    def is_accessible(self):
        return current_user.is_admin

class SmileyConfigView(ModelView):
    edit_modal = True
    create_modal = True
    
    column_list = ["replaces_text", "filename", "unlisted"]
    column_default_sort = ('replaces_text', False)
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js", 
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    column_labels = {
            'replaces_text': 'Emoticon Code',
            'filename': 'Smiley',
            'unlisted': 'Unlisted?'
        }
    
    column_formatters = {
            'filename': _smiley_image_formatter,
        }
        
    form_extra_fields = {
            'filename': form.ImageUploadField('Smiley', base_path=app.config["SMILEY_UPLOAD_DIR"], url_relative_path="smilies/"),
            'replaces_text': StringField()
        }
        
    def is_accessible(self):
        return current_user.is_admin
    
class AttachmentView(ModelView):
    can_create = False
    can_view_details = True
    can_edit = False

    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    column_list = ["owner", "path", "size_in_bytes", "created_date"]
    form_excluded_columns = ["owner", "character", "character_gallery","character_gallery_weight","character_avatar"]
        
    form_extra_fields = {
        'path': form.ImageUploadField('Attachment', base_path=app.config["ATTACHMENTS_UPLOAD_DIR"], url_relative_path="uploads/"),
    }
    
    column_default_sort = ('created_date', False)
    
    column_formatters = {
        'owner': _user_list_formatter,
        'path': _attachment_image_formatter,
        'created_date': _fancy_time_formatter,
        'size_in_bytes': _file_size_formatter
    }
    
    def is_accessible(self):
        return current_user.is_admin

class SwearFilterView(ModelView):
    page_size = 100
    
    form_extra_fields = {
        'replace_with': StringField()
    }
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    def create_model(self, form):
        """
            Create model from form.

            :param form:
                Form instance
        """
        try:
            _last_model = None
            for _word in form.word.data.split("\n"):
                model = self.model()
                model.replace_with = form.replace_with.data
                model.word = _word.lower().strip()
                self.session.add(model)
                self._on_model_change(form, model, True)
                self.session.commit()
                _last_model = model
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to create record.')

            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, True)

        return _last_model
    
    def is_accessible(self):
        return current_user.is_admin

class IPAddressView(ModelView):
    column_default_sort = ('last_seen', True)
    can_delete = True
    can_create = True
    edit_modal = True
    
    form_excluded_columns = ["user", "last_seen"]
    
    form_ajax_refs = {
        'user': StartsWithQueryAjaxModelLoader('user', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
    }
    
    column_formatters = {
        'user': _user_list_formatter,
        'last_seen': _fancy_time_formatter
    }
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
        
    def create_model(self, form):
        """
            Create model from form.

            :param form:
                Form instance
        """
        try:
            _last_model = None
            for _address in form.ip_address.data.split("\n"):
                model = self.model()
                model.banned = form.banned.data
                model.note = form.note.data
                model.ip_address = _address.lower().strip()
                self.session.add(model)
                self._on_model_change(form, model, True)
                self.session.commit()
                _last_model = model
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to create record.')

            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, True)

        return _last_model

    def is_accessible(self):
        return current_user.is_admin

class ThemeView(ModelView):
    form_extra_fields = {
            'additional_css': TextAreaField(),
            'profile_customization_css': TextAreaField()
        }
        
    def is_accessible(self):
        return current_user.is_admin

admin.add_view(ConfigurationView(sqlm.SiteConfiguration, sqla.session, name='General Options', category="Site", endpoint='configuration'))
admin.add_view(SmileyConfigView(sqlm.Smiley, sqla.session, name='Smiley List', category="Site", endpoint='smiley-configuration'))
admin.add_view(AttachmentView(sqlm.Attachment, sqla.session, name='Attachment List', category="Site", endpoint='attachments'))
admin.add_view(SwearFilterView(sqlm.SwearFilter, sqla.session, name='Swear Filtering', category="Site", endpoint='swear-filter'))
admin.add_view(IPAddressView(sqlm.IPAddress, sqla.session, name='IP Addresses', category="Site", endpoint='ip-addresses'))
admin.add_view(ThemeView(sqlm.SiteTheme, sqla.session, name='Theme Manager', category="Site", endpoint='site-themes'))

###################################################################################################
# Administrative views : Forum-specific options, settings, and config
###################################################################################################

class SectionView(ModelView):
    list_template = 'admin/model/section-list.html'
    can_delete = False
    action_disallowed_list = ['delete']
    form_excluded_columns = ["weight"]
    page_size = 1000

    form_ajax_refs = {
        'moderators': StartsWithQueryAjaxModelLoader('moderators', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
    }
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css",
        "/static/assets/Nestable2/jquery.nestable.min.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js", 
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js",
        "/static/assets/Nestable2/jquery.nestable.min.js"
        ]
        
    def is_accessible(self):
        return current_user.is_admin
        
    def get_query(self):
        return self.session.query(self.model).order_by("weight")
        
    @expose('/reorder', methods=('POST', ))
    def reorder_sections(self):
        request_json = request.get_json(force=True)
        
        current_order = 0
        for _section in request_json:
            try:
                section = sqlm.Section.query.filter_by(id=_section["id"])[0]
                section.weight = current_order
                current_order += 10
                sqla.session.add(section)
                sqla.session.commit()
            except IndexError:
                sqla.session.rollback()
        
        return "ok."

class CategoryView(ModelView):
    can_delete = False
    list_template = 'admin/model/category-list.html'
    page_size = 1000
    
    form_ajax_refs = {
        'moderators': StartsWithQueryAjaxModelLoader('moderators', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
        'restricted_users': StartsWithQueryAjaxModelLoader('restricted_users', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
    }
    
    form_excluded_columns = ["recent_post", "recent_topic", "section", "parent", "watchers", "topic_count", "post_count", "view_count", "children"]
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css",
        "/static/assets/Nestable2/jquery.nestable.min.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js", 
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js",
        "/static/assets/Nestable2/jquery.nestable.min.js"
        ]
    
    def get_query(self):
        return self.session.query(self.model).outerjoin(sqlm.Section) \
            .filter(sqlm.Category.parent_id == None) \
            .order_by(sqlm.Section.weight, sqlm.Category.weight)
    
    def order_category(self, cid, raw_json, section=None, parent=None, weight=0, weight_adjustment=0):
        weight += weight_adjustment
        try:
            category = sqlm.Category.query.filter_by(id=cid)[0]
        except IndexError:
            sqla.session.rollback()
            return
        print category
        
        category.weight = weight
        if section:
            category.section = section
            category.parent = None
            
        if parent:
            category.parent = parent
            category.section = None
            
        if raw_json.has_key("children"):
            _child_weight = 0
            for _child in raw_json["children"]:
                self.order_category(_child["id"], _child, section=None, parent=category , weight=_child_weight)
                _child_weight += 10
            
        sqla.session.add(category)
        sqla.session.commit()
        
    def is_accessible(self):
        return current_user.is_admin
        
    @expose('/toggle-view/<id>', methods=('POST', ))
    def toggle_view(self, id):
        try:
            category = sqlm.Category.query.filter_by(id=id)[0]
        except IndexError:
            sqla.session.rollback()
            return False
        
        if category.can_view_topics == None:
            category.can_view_topics = True
        
        category.can_view_topics = not category.can_view_topics
        
        sqla.session.add(category)
        sqla.session.commit()
        
        return "ok."
        
    @expose('/toggle-topics/<id>', methods=('POST', ))
    def toggle_topics(self, id):
        try:
            category = sqlm.Category.query.filter_by(id=id)[0]
        except IndexError:
            sqla.session.rollback()
            return False
        
        if category.can_create_topics == None:
            category.can_create_topics = True
        
        category.can_create_topics = not category.can_create_topics
        
        sqla.session.add(category)
        sqla.session.commit()
        
        return "ok."
        
    @expose('/toggle-posts/<id>', methods=('POST', ))
    def toggle_posts(self, id):
        try:
            category = sqlm.Category.query.filter_by(id=id)[0]
        except IndexError:
            sqla.session.rollback()
            return False
        
        if category.can_post_in_topics == None:
            category.can_post_in_topics = True
        
        category.can_post_in_topics = not category.can_post_in_topics
        
        sqla.session.add(category)
        sqla.session.commit()
        
        return "ok."
        
    @expose('/reorder', methods=('POST', ))
    def reorder_categories(self):
        request_json = request.get_json(force=True)
        
        for _section in request_json:
            _category_weight = 0
            try:
                section = sqlm.Section.query.filter_by(id=_section["id"])[0]
            except IndexError:
                sqla.session.rollback()
                continue
            
            for _category in _section["children"]:
                self.order_category(_category["id"], _category, section=section, weight=_category_weight)
                _category_weight += 10
                
            print section
        
        return "ok."

class CategoryPermissionOverrideView(ModelView):
    def is_accessible(self):
        return current_user.is_admin

class RoleEditorView(ModelView):
    column_list = ["name", "role",]
    
    column_formatters = {
        'role': _role_formatter,
    }
        
    form_ajax_refs = {
        'users': StartsWithQueryAjaxModelLoader('users', sqla.session, sqlm.User, fields=['display_name',], page_size=10),
    }
    
        
    column_labels = {
        'role': "Display",
    }
    
    def is_accessible(self):
        return current_user.is_admin

class UserAdministrationView(ModelView):
    can_create = False
    edit_template = 'admin/model/edit_user.html'
    
    column_list = ["display_name", "email_address", "joined", "last_seen", "last_seen_ip_address", "is_mod", "is_admin"]
    column_filters = ["display_name","is_mod", "is_admin"]
    
    form_edit_rules = ("display_name", "login_name","email_address", "is_admin", "is_mod", "can_mod_forum", 
        "can_mod_blogs", "can_mod_user_profiles", "can_mod_status_updates")
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
    
    column_formatters = {
        'role': _role_formatter,
        'joined': _fancy_time_formatter,
        'last_seen': _fancy_time_formatter
    }
    
    def is_accessible(self):
        return current_user.is_admin
    
class StaffView(ModelView):
    can_create = False
    
    column_list = ["display_name", "is_admin", "is_mod", "can_mod_forum", 
        "can_mod_blogs", "can_mod_user_profiles", "can_mod_status_updates", "get_modded_areas"]
    column_filters = ["display_name",]
    form_create_rules = ("display_name", "is_admin", "is_mod", "can_mod_forum", 
        "can_mod_blogs", "can_mod_user_profiles", "can_mod_status_updates")
    form_edit_rules = ("display_name", "is_admin", "is_mod", "can_mod_forum", 
        "can_mod_blogs", "can_mod_user_profiles", "can_mod_status_updates")
    
    extra_css = ["/static/assets/datatables/dataTables.bootstrap.css",
        "/static/assets/datatables/dataTables.responsive.css"
        ]
    extra_js = ["/static/assets/datatables/js/jquery.dataTables.min.js",
        "/static/assets/datatables/dataTables.bootstrap.js",
        "/static/assets/datatables/dataTables.responsive.js"
        ]
    
    column_formatters = {
        'display_name': _user_formatter,
        'get_modded_areas': _unslugify_list_formatter
    }
    
    def get_query(self):
        return self.session.query(self.model).filter(
                            sqla.or_(
                                self.model.is_mod == True,
                                self.model.is_admin == True
                            )
                        )
    
    def get_count_query(self):
        return self.session.query(sqla.func.count('*')).select_from(self.model).filter(
                            sqla.or_(
                                self.model.is_mod == True,
                                self.model.is_admin == True
                            )
                        )
    
    def is_accessible(self):
        return current_user.is_admin

admin.add_view(SectionView(sqlm.Section, sqla.session, name='Sections', category="Forum", endpoint='sections'))
admin.add_view(CategoryView(sqlm.Category, sqla.session, name='Categories', category="Forum", endpoint='categories'))
admin.add_view(CategoryPermissionOverrideView(sqlm.CategoryPermissionOverride, sqla.session, name='Permission Overrides', category="Forum", endpoint='perm-overrides'))
admin.add_view(RoleEditorView(sqlm.Role, sqla.session, name='User Roles', category="Forum", endpoint='roles'))
admin.add_view(UserAdministrationView(sqlm.User, sqla.session, name='Manage Users', category="Forum", endpoint='manage-users'))
admin.add_view(StaffView(sqlm.User, sqla.session, name='Manage Staff', category="Forum", endpoint='manage-staff'))

# TODO Moderation
# TODO Add ajax view for creating infraction
# TODO Add ajax view for modifying a ban
# TODO Add chart to the front showing reports vs infractions
# TODO Show recent moderation alerts
# TODO Log all moderation actions
# TODO Verify that all front end moderation actions are working
# TODO Add mod actions that are missing
# TODO Add status reply mod actions
# TODO Add code for jump to status reply
# TODO Write burning board status import script