from flask import Flask
from flask.ext.mongoengine import MongoEngine, MongoEngineSessionInterface
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.admin import Admin
from flask.ext.redis import FlaskRedis
from os import path

REDIS_URL = "redis://127.0.0.1:6379/0"

app = Flask(__name__)
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
login_manager = LoginManager()
login_manager.init_app(app)
app.config["MONGODB_SETTINGS"] = {'DB': "woe_main"}
app.config["SECRET_KEY"] = "woe"
app.config["AVATAR_UPLOAD_DIR"] = path.join(app.root_path, 'static', 'avatars')
app.config["MAX_CONTENT_LENGTH"] = 1000000000

db = MongoEngine(app)
app.session_interface = MongoEngineSessionInterface(db)
bcrypt = Bcrypt(app)
redis_store = FlaskRedis(app)

import utilities
import views.core
import views.topics
import views.dashboard
import views.profiles
import views.admin

if __name__ == '__main__':
    app.run()
