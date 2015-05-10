from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators
from woe.models.core import User

class LoginForm(Form):
    username = StringField('Username', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired()])
            
    def __get_user__(self, login_name):
        return User.objects(login_name=login_name)
    
    def validate_username(self, field):
        if not self.__get_user__(field.data.lower().strip()):
            raise validators.ValidationError("Invalid username or password.")
            
    def validate_password(self, field):
        user = self.__get_user__(self.username.data.lower().strip())
        if not user:
            raise validators.ValidationError("Invalid username or password.")
            
        if not user[0].check_password(field.data.strip()):
            raise validators.ValidationError("Invalid username or password.")
        
        self.user = user[0]