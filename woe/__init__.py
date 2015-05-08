from flask import Flask
from flask.ext.mongoengine import MongoEngine


app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "woe_main"}
app.config["SECRET_KEY"] = "woe"

db = MongoEngine(app)

import views.topics

if __name__ == '__main__':
    app.run()
