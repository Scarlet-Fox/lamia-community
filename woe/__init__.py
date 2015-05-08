from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.bcrypt import Bcrypt

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "woe_main"}
app.config["SECRET_KEY"] = "woe"

db = MongoEngine(app)
bcrypt = Bcrypt(app)

import views.topics

if __name__ == '__main__':
    app.run()
