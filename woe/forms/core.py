from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField
from woe.models.core import User
from flask_wtf.file import FileField, FileAllowed, FileRequired
from PIL import Image

class RegistrationForm(Form):
    username = StringField('Username', [validators.InputRequired(),
        validators.Regexp("[A-Za-z\s0-9]", message="Your first username should be letters, numbers, and maybe a space. You can change how it looks to others, later.")]) # TODO Regex validate
    password = PasswordField('Password', [validators.InputRequired()])
    confirm_password = PasswordField('Confirm Password', [validators.InputRequired()])
    email = StringField('Email Address', [validators.Email(), validators.InputRequired()])
    question  = SelectField('Fill in the blank : Twilight Sparkle is __________.', choices=[
        ('kaiju', 'a kaiju'), 
        ('pony', 'a pony'), 
        ('zoop', 'secretly pink')])
        
    def validate_username(self, field):
        user_count = len(User.objects(login_name=field.data.lower().strip())) + len(User.objects(display_name__iexact=field.data.strip()))
        if user_count > 0:
            raise validators.ValidationError("Your username is already taken.")
    
    def validate_email(self, field):
        user_count = len(User.objects(email_address=field.data.strip().lower()))
        if user_count > 0:
            raise validators.ValidationError("Your email address is already in use by another account.")
                
    def validate_question(self, field):
        if field.data != "pony":
            raise validators.ValidationError("You filled in the blank with the wrong thing. Are you a robot?")
    
    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise validators.ValidationError("Password and confirmation must match.")
    
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
        
        print field.data.strip()
        if not user[0].check_password(field.data.strip()):
            raise validators.ValidationError("Invalid username or password.")
        
        self.user = user[0]
        if self.user.validated == False:
            raise validators.ValidationError("Your account is being validated, give us a moment. :)")
            
        if self.user.banned == True:
            raise validators.ValidationError("I'm sorry, I'm so sorry, but it looks like you're banned.")
        

class DisplayNamePasswordForm(Form):
    display_name = StringField('Display Name')
    email = StringField('Email Address', [validators.Email()])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password')
    confirm_new_password = PasswordField('Confirm New Password')
    
    def validate_display_name(self, field):
        user_count = len(User.objects(display_name__iexact=field.data.strip()))
        if user_count > 0:
            raise validators.ValidationError("That name is already taken.")
    
    def validate_current_password(self, field):
        if not self.user_object.check_password(field.data) and self.current_user.is_staff == False:
            raise validators.ValidationError("Please enter your current password to change your account details.")
    
    def validate_confirm_new_password(self, field):
        if field.data != self.new_password.data:
            raise validators.ValidationError("Password and confirmation must match.")
    
class AvatarTitleForm(Form):
    avatar = FileField('Avatar', 
            [FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only jpg, png, and gifs allowed.')]
        )
    title = StringField('Member Title', [validators.Length(0,150)])
    
    def validate_avatar(self, field):
        if not field.data:
            return
        
        file = field.data
        image = Image.open(file)
        xsize, ysize = image.size
        extension = field.data.filename.split(".")[-1]
        
        if extension == "gif" and (xsize > 200 or ysize > 200):
            raise validators.ValidationError("Your animated image is too large. (Resize to less than 200x200.)")
            
        if xsize > 200 or ysize > 200:
            resize_measure = min(200.0/float(xsize),200.0/float(ysize))
            self.avatar_image = image.copy()
            self.avatar_image.thumbnail([xsize*resize_measure,ysize*resize_measure])
        else:
            self.avatar_image = image
            
        print len(file.read()) 
        if len(file.read()) > 256*1024:
            raise validators.ValidationError("Your avatar filesize is too large. (Resize to less than 256kb.)")
        
        resize_measure = min(40.0/float(xsize),40.0/float(ysize))
        self.fourty_image = image.copy()
        self.fourty_image.thumbnail([xsize*resize_measure,ysize*resize_measure]) 
        
        resize_measure = min(60.0/float(xsize),60.0/float(ysize))
        self.sixty_image = image.copy()
        self.sixty_image.thumbnail([xsize*resize_measure,ysize*resize_measure])

        if extension == "gif":
            self.gif = True
        else:
            self.gif = False
        
