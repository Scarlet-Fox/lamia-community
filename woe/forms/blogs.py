from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField, HiddenField
from woe.models.core import User, IPAddress
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wand.image import Image
import shutil, pytz, arrow

class BlogSettingsForm(Form):
    title = StringField('Blog Name', [validators.InputRequired()], default="")
    description = StringField('Description', [validators.InputRequired()], default="")
    privacy_setting = SelectField('Privacy Setting', choices=[
            ("all", "Everyone"),
            ("members", "Only Members"),
            ("friends", "Only Friends"),
            ("editors", "Only Editors"),
            ("you", "Only You")
        ], default="members")
    