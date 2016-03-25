from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField, HiddenField, TextField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wand.image import Image
import shutil, pytz, arrow

class NewSignature(Form):
    name = StringField('Nickname', [validators.InputRequired()], default="")
    html = HiddenField('Signature', [validators.InputRequired()], default="")
    active = BooleanField('Active?', default=False)
