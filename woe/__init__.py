try:
    from psycopg2cffi import compat
    compat.register()
except ImportError:
    pass

from werkzeug.contrib.fixers import ProxyFix
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.admin import Admin
from flask.ext.cache import Cache
from flask.ext.assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from flask import session
from flask.ext.session import Session
from bson.dbref import DBRef
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

app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = sqla
Session(app)

assets = Environment(app)
app.config['ASSETS_DEBUG'] = settings_file["asset_debug"]

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
bcrypt = Bcrypt(app)
if settings_file.get("toolbar", False):
    toolbar = DebugToolbarExtension(app)

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        raise ImportError

import datetime
from bson.objectid import ObjectId
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

# import tasks
import sqlmodels
import views.core
import views.blogs
import views.roleplay
import views.forum
import views.dashboard
import views.profiles
import views.admin
import views.private_messages
import views.search
import views.status_updates
import utilities
import email_utilities

if __name__ == '__main__':
    app.run()
