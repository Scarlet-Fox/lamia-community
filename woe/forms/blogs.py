from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField, HiddenField, TextField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wand.image import Image
import shutil, pytz, arrow

class BlogSettingsForm(Form):
    title = StringField('Blog Name', [validators.InputRequired()], default="")
    description = HiddenField('Description', [validators.InputRequired()], default="")
    privacy_setting = SelectField('Privacy Setting', choices=[
            ("all", "Everyone"),
            ("members", "Only Members"),
            ("friends", "Only Friends"),
            ("editors", "Only Editors"),
            ("you", "Only You")
        ], default="members")

class BlogEntryForm(Form):
    title = StringField('Title', [validators.InputRequired()], default="")
    entry = HiddenField('Post', [validators.InputRequired()], default="")
    draft = BooleanField('Draft / Mark as Hidden?', default=False)

class BlogCommentForm(Form):
    comment = HiddenField('Comment', [validators.InputRequired()], default="")
