from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField, HiddenField
from woe.models.core import User, IPAddress
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wand.image import Image
import shutil, pytz, arrow

class CharacterForm(Form):
    name = StringField('Name', [validators.InputRequired(),])
    age = StringField('Age')
    species = StringField('Species')
    motto = StringField('Motto')
    appearance = HiddenField('Appearance')
    personality = HiddenField('Personality')
    backstory = HiddenField('Backstory')
    other = HiddenField('Other')