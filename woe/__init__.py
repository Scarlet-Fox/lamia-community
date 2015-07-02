from werkzeug.contrib.fixers import ProxyFix
from flask import Flask
from flask.ext.mongoengine import MongoEngine, MongoEngineSessionInterface
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.admin import Admin
from flask.ext.cache import Cache
from flask.ext.assets import Environment, Bundle
from bson.dbref import DBRef
from os import path
import json

settings_file = json.loads(open("config.json").read())

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
login_manager = LoginManager()
login_manager.init_app(app)
app.config["MONGODB_SETTINGS"] = {'DB': settings_file["database"]}
app.config["SECRET_KEY"] = settings_file["secret_key"]
app.config["AVATAR_UPLOAD_DIR"] = path.join(app.root_path, 'static', 'avatars')
app.config["MAX_CONTENT_LENGTH"] = 1000000000
app.config['DEBUG'] = settings_file["debug"]
app.settings_file = settings_file

assets = Environment(app)
app.config['ASSETS_DEBUG'] = settings_file["asset_debug"]

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
db = MongoEngine(app)
app.session_interface = MongoEngineSessionInterface(db)
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
 
class MongoJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            return unicode(obj)
        elif isinstance(obj, DBRef):
            return unicode(obj.id)
                
        try:
            return json.JSONEncoder.default(self, obj)
        except:
            return ""
app.MongoJsonEncoder = MongoJsonEncoder
def jsonify(*args, **kwargs):
    """ jsonify with support for MongoDB ObjectId
    """
    return Response(json.dumps(dict(*args, **kwargs), cls=MongoJsonEncoder), mimetype='application/json')

app.jsonify = jsonify

# import tasks
import models.core
import models.forum
import models.roleplay
import views.core
import views.forum
import views.dashboard
import views.profiles
import views.admin
import views.private_messages
import views.search
import views.status_updates
import utilities

if __name__ == '__main__':
    app.run()
