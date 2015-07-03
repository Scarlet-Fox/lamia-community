from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField, HiddenField
from woe.models.core import User, IPAddress
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wand.image import Image
import shutil, pytz, arrow

class CharacterForm(Form):
    name = StringField('Name', [validators.InputRequired(),])
    age = StringField('Age', default="")
    species = StringField('Species', default="")
    motto = StringField('Motto', default="")
    appearance = HiddenField('Appearance', default="")
    personality = HiddenField('Personality', default="")
    backstory = HiddenField('Backstory', default="")
    other = HiddenField('Other', default="")