from flask import Flask
from flask.ext.mongoengine import MongoEngine, MongoEngineSessionInterface
import json

settings_file = json.loads(open("config.json").read())

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': settings_file["database"]}
db = MongoEngine(app)
