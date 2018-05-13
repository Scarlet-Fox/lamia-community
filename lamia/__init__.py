# -*- coding: utf-8 -*-

###############################################################################
# Misc patching
###############################################################################

try:
    from psycopg2cffi import compat
    compat.register()
except ImportError:
    pass

from sqlalchemy.orm.util import identity_key
from flask_admin.contrib.sqla.fields import text_type

from flask_admin.contrib.sqla import fields
from wtforms.ext.sqlalchemy import fields as wtfs_fields


def get_pk_from_identity(obj):
    res = identity_key(instance=obj)
    cls, key = res[0], res[1]
    return text_type(':'.join(text_type(x) for x in key))

fields.get_pk_from_identity = get_pk_from_identity
wtfs_fields.get_pk_from_identity = get_pk_from_identity

###############################################################################
# The actual app
###############################################################################



from werkzeug.contrib.fixers import ProxyFix
from werkzeug.contrib.cache import RedisCache
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_admin import Admin
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from flask import session
from flask_session import Session
from os import path
import json

settings_file = json.loads(open("config.json").read())
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config["SECRET_KEY"] = settings_file["secret_key"]
app.secret_key = settings_file["secret_key"]
app.config["AVATAR_UPLOAD_DIR"] = path.join(app.root_path, 'static', 'avatars')
app.config["MAKO_EMAIL_TEMPLATE_DIR"] = path.join(app.root_path, 'templates', 'email')
app.config["DEFAULT_TEMPLATE_DIR"] = path.join(app.root_path, 'templates')
app.config["CUSTOMIZATIONS_UPLOAD_DIR"] = path.join(app.root_path, 'static', 'customizations')
app.config["SMILEY_UPLOAD_DIR"] = path.join(app.root_path, 'static', 'smilies')
app.config["ATTACHMENTS_UPLOAD_DIR"] = path.join(app.root_path, 'static', 'uploads')
app.config["MAX_CONTENT_LENGTH"] = 1000000000
app.config['DEBUG'] = settings_file["debug"]
app.config['TEMPLATES_AUTO_RELOAD'] = settings_file["debug"]
# app.config['SQLALCHEMY_ECHO'] = settings_file["debug"]
app.config['BASE'] = settings_file["base_url"]
app.config['MGAPI'] = settings_file["mailgun_api"]
app.config['LISTENER'] = settings_file["listener"]
app.config['LISTENER_PATH'] = settings_file["listener_path"]
app.config['SQLALCHEMY_DATABASE_URI'] = settings_file["alchemy_uri"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
sqla = SQLAlchemy(app)
app.sqla = sqla
app.settings_file = settings_file

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
app.jinja_env.cache = {}

#cache = FileSystemCache(cache_dir=path.join(app.root_path, 'cache'))
class LamiaRedisCache(RedisCache):
    def get_w_default(self, key, default):
        value = self.get(key)
        if value is not None:
            return value
        else:
            return default

cache = LamiaRedisCache()

app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = sqla
Session(app)

assets = Environment(app)
app.config['ASSETS_DEBUG'] = settings_file["asset_debug"]

bcrypt = Bcrypt(app)

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        raise ImportError

import datetime
from werkzeug import Response

class SallyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()

        try:
            return json.JSONEncoder.default(self, obj)
        except:
            return ""
app.SallyJsonEncoder = SallyJsonEncoder
def jsonify(*args, **kwargs):
    return Response(json.dumps(dict(*args, **kwargs), cls=SallyJsonEncoder), mimetype='application/json')

app.jsonify = jsonify

# imports
from . import sqlmodels
from .views import core
from .views import blogs
from .views import roleplay
from .views import forum
from .views import dashboard
from .views import profiles
from .views import admin
from .views import private_messages
from .views import search
from .views import status_updates
from .views import api
from . import utilities
from . import email_utilities

###############################################################################
# Task management with Celery
###############################################################################

from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

app.config.update(
    CELERY_BROKER_URL=settings_file["celery_broker_url"],
    CELERY_RESULT_BACKEND=settings_file["celery_result_backend"]
)

celery = make_celery(app)
app.celery = celery
from . import tasks

###############################################################################
# Black magic for template overloading
###############################################################################

from jinja2 import FileSystemLoader
from jinja2.loaders import split_template_path
from flask_login import current_user
from jinja2.exceptions import TemplateNotFound
from jinja2.utils import open_if_exists, internalcode
import time, weakref, types

@internalcode
def _lamia_load_template(self, name, globals):
    if self.loader is None:
        raise TypeError('no loader for this environment specified')
    
    theme_name = ""
    if current_user.is_authenticated:
        if current_user.theme:
            if current_user.theme.directory_name:
                theme_name = current_user.theme.directory_name
        
    cache_key = (weakref.ref(self.loader), name, theme_name)
    if self.cache is not None:
        template = self.cache.get(cache_key)
        if template is not None and (not self.auto_reload or
                                     template.is_up_to_date):
            return template
    template = self.loader.load(self, name, globals)
    if self.cache is not None:
        self.cache[cache_key] = template
    return template

app.jinja_env._load_template = types.MethodType(_lamia_load_template, app.jinja_env)

class LamiaThemeFileSystemLoader(FileSystemLoader):
    def __init__(self, *args, **kwargs):
        return super(LamiaThemeFileSystemLoader, self).__init__(*args, **kwargs)

    def get_source(self, environment, template):
        searchpaths = self.searchpath[:]
        use_theme_template = False
        pieces = split_template_path(template)
        if current_user.is_authenticated:
            if current_user.theme and current_user.theme.directory_name:
                theme_pieces = pieces[:]
                theme_pieces[-1] = current_user.theme.directory_name+"-"+theme_pieces[-1]
                theme_path = path.join(app.config["DEFAULT_TEMPLATE_DIR"], "themes", current_user.theme.directory_name, *theme_pieces)
                if path.exists(theme_path):
                    use_theme_template = True

        for searchpath in searchpaths:
            if use_theme_template:
                filename = theme_path
            else:
                filename = path.join(searchpath, *pieces)
            f = open_if_exists(filename)

            if f is None:
                continue
            try:
                contents = f.read().decode(self.encoding)
            finally:
                f.close()

            mtime = path.getmtime(filename)
            
            def uptodate():
                try:
                    return path.getmtime(filename) == mtime
                except OSError:
                    return False
            return contents, filename, uptodate
        raise TemplateNotFound(template)

app.jinja_loader = LamiaThemeFileSystemLoader(app.config["DEFAULT_TEMPLATE_DIR"])

###############################################################################
# Something incredibly amazing, yet quite boring
###############################################################################

if __name__ == '__main__':
    app.run()
