from flask import Flask
from flask.ext.mongoengine import MongoEngine, MongoEngineSessionInterface
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.admin import Admin
from flask.ext.cache import Cache
from os import path

app = Flask(__name__)
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
login_manager = LoginManager()
login_manager.init_app(app)
app.config["MONGODB_SETTINGS"] = {'DB': "woe_main"}
app.config["SECRET_KEY"] = "woe"
app.config["AVATAR_UPLOAD_DIR"] = path.join(app.root_path, 'static', 'avatars')
app.config["MAX_CONTENT_LENGTH"] = 1000000000
app.config['DEBUG'] = True

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
db = MongoEngine(app)
app.session_interface = MongoEngineSessionInterface(db)
bcrypt = Bcrypt(app)

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
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    """ jsonify with support for MongoDB ObjectId
    """
    return Response(json.dumps(dict(*args, **kwargs), cls=MongoJsonEncoder), mimetype='application/json')

app.jsonify = jsonify

import utilities
import views.core
import views.forum
import views.dashboard
import views.profiles
import views.admin
import views.private_messages

if __name__ == '__main__':
    app.run()
