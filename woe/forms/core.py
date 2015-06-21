from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField
from woe.models.core import User, IPAddress
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wand.image import Image
import shutil, pytz, arrow

class ResetPasswordForm(Form):
    password = PasswordField('Password', [validators.InputRequired()])
    confirm_password = PasswordField('Confirm Password', [validators.InputRequired()])
    
    def validate_password(self, field):
        if arrow.get(self.user.password_forgot_token_date).datetime < arrow.utcnow().replace(hours=-3).datetime:
            raise validators.ValidationError("Your token has expired. You can get a new one by <a href=\"/forgot-password\">clicking here</a>.")
    
    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise validators.ValidationError("Password and confirmation must match.")
    
class ForgotPasswordForm(Form):
    email_address = StringField('Email address', [validators.Email(), validators.InputRequired()])
    
    def validate_email_address(self, field):
        try:
            self.user = User.objects(email_address=field.data)[0]
        except:
            raise validators.ValidationError("Invalid email address. You may want to contact us at community@worldofequestria.com if you can't remember.")

class UserSettingsForm(Form):
    TIMEZONE_CHOICES = [(z, z) for z in pytz.common_timezones]
    time_zone = SelectField('Time zone', choices=TIMEZONE_CHOICES)
    
    def validate_time_zone(self, field):
        if field.data not in pytz.common_timezones:
            raise validators.ValidationError("Invalid time zone.")

class RegistrationForm(Form):
    username = StringField('Username', [validators.InputRequired(),
        validators.Regexp("[A-Za-z\s0-9]", message="Your first username should be letters, numbers, and maybe a space. You can change how it looks to others, later.")])
    password = PasswordField('Password', [validators.InputRequired()])
    confirm_password = PasswordField('Confirm Password', [validators.InputRequired()])
    email = StringField('Email Address', [validators.Email(), validators.InputRequired()])
    question  = SelectField('Fill in the blank : Twilight Sparkle is __________.', choices=[
        ('kaiju', 'a kaiju'), 
        ('pony', 'a pony'), 
        ('darkestdungeon', 'an eldritch abomination')])
    over_thirteen = BooleanField('Are you at or above the age of 13?')
    
    def validate_over_thirteen(self, field):
        if not field.data:
            raise validators.ValidationError("We cannot accept registrations from users under 13 years old. This is the law. If you like this site, come back when you're over 13.")
    
    def validate_username(self, field):
        ip_addresses = IPAddress.objects(ip_address=self.ip)
        for address in ip_addresses:
            if address.user.banned:
                raise validators.ValidationError("It looks like your account was banned, please don't re-register. If this is a mistake, contact community-@-worldofequestria.com (remove the dashes).")
        
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
        
        if not user[0].check_password(field.data.strip()):
            raise validators.ValidationError("Invalid username or password.")
        
        self.user = user[0]
        if self.user.validated == False:
            raise validators.ValidationError("Your account is being validated, give us a moment. :)")

class DisplayNamePasswordForm(Form):
    display_name = StringField('Display Name')
    email = StringField('Email Address', [validators.Email()])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password')
    confirm_new_password = PasswordField('Confirm New Password')
    
    def validate_display_name(self, field):
        if self.user_object.display_name != field.data.strip():
            user_count = len(User.objects(display_name__iexact=field.data.strip()))
            if user_count > 0:
                raise validators.ValidationError("That name is already taken.")
    
    def validate_current_password(self, field):
        if not self.user_object.check_password(field.data) and self.current_user.is_admin == False:
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
        
        image = Image(file=file)
        xsize = image.width
        ysize = image.height
        extension = field.data.filename.split(".")[-1]
            
        if xsize > 200 or ysize > 200:
            resize_measure = min(200.0/float(xsize),200.0/float(ysize))
            self.avatar_image = image.clone()
            self.avatar_image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure)))
        else:
            self.avatar_image = image
        
        resized_avatar = self.avatar_image.clone()
        resized_avatar_bin = self.avatar_image.make_blob()
        avvie_size = len(resized_avatar_bin)
        if avvie_size > 512*1024:
            raise validators.ValidationError("Your avatar filesize (even after being resized) is too large. Resize to less than 512kb.")
        
        resize_measure = min(40.0/float(xsize),40.0/float(ysize))
        self.fourty_image = image.clone()
        self.fourty_image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure)))
        
        resize_measure = min(60.0/float(xsize),60.0/float(ysize))
        self.sixty_image = image.clone()
        self.sixty_image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure)))        
