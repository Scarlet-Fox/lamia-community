from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators, SelectField, HiddenField, IntegerField, DateField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wand.image import Image, GRAVITY_TYPES
import shutil, pytz, arrow
from lamia import sqla
import lamia.sqlmodels as sqlm

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
            self.user = sqla.session.query(sqlm.User).filter_by(email_address=field.data)[0]
        except:
            raise validators.ValidationError("Invalid email address. You may want to contact us at help@casualanime.com if you can't remember.")

class UserSettingsForm(Form):
    TIMEZONE_CHOICES = [(z, z) for z in pytz.common_timezones]
    time_zone = SelectField('Time zone', choices=TIMEZONE_CHOICES)
    no_images = BooleanField("Hide all images (super at-work mode)")
    navbar_top = BooleanField("Use sticky navbar")
    no_emails = BooleanField("Mute all emails (no email notifications)")
    notification_sound = BooleanField("Play sound for new notifications")
    all_notification_sounds = BooleanField("Play sound for all notifications (instead of just the first one)")
    minimum_time_between_emails = IntegerField("Minimum time between notification emails (in minutes, no less than 5 and no more than 1440)",
            [validators.InputRequired(), validators.NumberRange(5,1440)]
        )
    
    try:
        THEME_CHOICES = [(str(t.id), t.name) for t in sqla.session.query(sqlm.SiteTheme).order_by(sqlm.SiteTheme.weight).all()]
    except:
        THEME_CHOICES = []
    theme = SelectField('Theme', choices=THEME_CHOICES)
    birthday = DateField('Birthday', format='%m/%d/%Y', validators=(validators.Optional(),))

    def validate_time_zone(self, field):
        if field.data not in pytz.common_timezones:
            raise validators.ValidationError("Invalid time zone.")

    def validate_theme(self, field):
        try:
            self.theme_object = sqla.session.query(sqlm.SiteTheme).filter_by(id=field.data)[0]
        except:
            sqla.session.rollback()
            raise validators.ValidationError("Invalid theme.")

class RegistrationForm(Form):
    username = StringField('Username', [validators.InputRequired(),
        validators.Length(max=30),
        validators.Regexp("[A-Za-z\s0-9]", message="Your first username should be letters, numbers, and maybe a space. You can change how it looks to others, later.")])
    password = PasswordField('Password', [validators.InputRequired()])
    confirm_password = PasswordField('Confirm Password', [validators.InputRequired()])
    email = StringField('Email Address', [validators.Email(), validators.InputRequired()])
    question  = SelectField('What color is the sky, on a bright and sunny day?', choices=[
        ('purple', 'purple'),
        ('blue', 'blue'),
        ('darkestdungeon', 'an eldritch abomination')])
    over_thirteen = BooleanField('Are you at or above the age of 13?')
    how_did_you_find_us = StringField('How did you find us?', [validators.InputRequired(),])
    redirect_to = HiddenField('Next')

    def validate_over_thirteen(self, field):
        if not field.data:
            raise validators.ValidationError("We cannot accept registrations from users under 13 years old. This is the law. If you like this site, come back when you're over 13.")

    def validate_username(self, field):
        ip_addresses = sqla.session.query(sqlm.IPAddress).filter_by(ip_address=self.ip).all()
        for address in ip_addresses:
            if address.user.banned:
                raise validators.ValidationError("It looks like your account was banned, please don't re-register. If this is a mistake, contact help-@-casualanime.com (remove the dashes).")

        user_count = sqla.session.query(sqlm.User).filter_by(
            login_name=field.data.lower().strip()
        ).count() + sqla.session.query(sqlm.User).filter(
            sqla.func.lower(sqlm.User.display_name) == sqla.func.lower(field.data.lower().strip())
        ).count()

        if user_count > 0:
            raise validators.ValidationError("Your username is already taken.")

    def validate_email(self, field):
        user_count = sqla.session.query(sqlm.User).filter_by(
            email_address=field.data.strip().lower()
        ).count()
        if user_count > 0:
            raise validators.ValidationError("Your email address is already in use by another account.")

    def validate_question(self, field):
        if field.data != "blue":
            raise validators.ValidationError("You answered with the wrong thing. Are you a robot?")

    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise validators.ValidationError("Password and confirmation must match.")

class LoginForm(Form):
    username = StringField('Username', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired()])
    anonymouse = BooleanField('Anonymous login?')
    redirect_to = HiddenField('Next')

    def __get_user__(self, login_name):
        try:
            return sqla.session.query(sqlm.User).filter_by(login_name=login_name)[0]
        except IndexError:
            return None

    def validate_username(self, field):
        if not self.__get_user__(field.data.lower().strip()):
            raise validators.ValidationError("Invalid username or password.")

    def validate_password(self, field):
        user = self.__get_user__(self.username.data.lower().strip())

        if not user:
            raise validators.ValidationError("Invalid username or password.")

        if not user.check_password(field.data.strip()):
            raise validators.ValidationError("Invalid username or password.")

        self.user = user
        if self.user.validated == False:
            raise validators.ValidationError("Please confirm your account before login - check your email for the confirmation message!")

    def validate_redirect_to(self, field):
        if not field.data.strip() == "":
            if not field.data.startswith("/"):
                raise validators.ValidationError("Improper redirect.")

class DisplayNamePasswordForm(Form):
    display_name = StringField('Display Name', [validators.Length(max=30),])
    email = StringField('Email Address', [validators.Email()])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password')
    confirm_new_password = PasswordField('Confirm New Password')

    def validate_display_name(self, field):
        if self.user_object.display_name != field.data.strip():
            user_count = sqla.session.query(sqlm.User).filter(
                sqla.func.lower(sqlm.User.display_name) == field.data.lower().strip()
            ).count()
            if user_count > 0:
                raise validators.ValidationError("That name is already taken.")

    def validate_email(self, field):
        if self.user_object.email_address != field.data.strip():
            user_count = sqla.session.query(sqlm.User).filter_by(
                email_address=field.data.strip().lower()
            ).count()
            if user_count > 0:
                raise validators.ValidationError("Your email address is already in use by another account.")

    def validate_current_password(self, field):
        if not self.current_user.is_admin:
            if not self.user_object.check_password(field.data):
                raise validators.ValidationError("Please enter your current password to change your account details.")

    def validate_confirm_new_password(self, field):
        if field.data != self.new_password.data:
            raise validators.ValidationError("Password and confirmation must match.")

class SiteCustomizationForm(Form):
    banner = FileField('Page Banner Image',
            [FileAllowed(['jpg', 'jpeg', 'png'], 'Only jpg and png allowed.')]
        )
    header = FileField('Header Background Image',
            [FileAllowed(['jpg', 'jpeg', 'png'], 'Only jpg and png allowed.')]
        )
    background_image = FileField('Page Background Image',
            [FileAllowed(['jpg', 'jpeg', 'png'], 'Only jpg and png allowed.')]
        )
        
    background = StringField('Page Background Color', [validators.Regexp('^([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^$', message="Only valid hexcodes are supported.")])

    header_background = StringField('Header Background Color', [validators.Regexp('^([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^$', message="Only valid hexcodes are supported.")])
    header_text_color = StringField('Header Text Color', [validators.Regexp('^([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^$', message="Only valid hexcodes are supported.")])
    header_text_shadow_color = StringField('Header Text Shadow Color', [validators.Regexp('^([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^$', message="Only valid hexcodes are supported.")])
    use_text_shadow = BooleanField('Use Header Text Shadow')

    def validate_background_image(self, field):
        if not field.data:
            return

        file = field.data
        image = Image(file=file)
        
        _blob =  image.make_blob()
        
        if len(_blob) > 1024*1024*3:
            raise validators.ValidationError("Your background image filesize is too large. Resize to less than 3 MB.")

        self.background_image_file = image
        
    def validate_banner(self, field):
        if not field.data:
            return

        file = field.data
        image = Image(file=file)

        if image.height > 460:
            self.banner_height = 460
        else:
            self.banner_height = image.height

        _blob =  image.make_blob()
        if len(_blob) > 1024*1024*2:
            raise validators.ValidationError("Your banner filesize is too large. Resize to less than 2 MB.")

        self.banner_image = image

    def validate_header(self, field):
        if not field.data:
            return

        file = field.data
        image = Image(file=file)
        _blob =  image.make_blob()
        if len(_blob) > 1024*300:
            raise validators.ValidationError("Your header filesize is too large. Resize to less than 300 KB.")

        self.header_image = image

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
        
        crop_off_bottom = False
        crop_off_right = False
        if ysize > xsize:
            crop_off_bottom = True
            pixels_to_crop = ysize - xsize
        elif xsize > ysize:
            crop_off_right = True
            pixels_to_crop = xsize - ysize

        self.fourty_image = image.clone()
        if crop_off_bottom == True:
            self.fourty_image.crop(height=(ysize-pixels_to_crop))
        if crop_off_right == True:
            self.fourty_image.crop(width=(xsize-pixels_to_crop), gravity='center', height=ysize)
            
        self.fourty_image.resize(int(round(40)),int(round(40)))

        self.sixty_image = image.clone()
        if crop_off_bottom == True:
            self.sixty_image.crop(height=(ysize-pixels_to_crop))
        if crop_off_right == True:
            self.sixty_image.crop(width=(xsize-pixels_to_crop), gravity='center', height=ysize)
            
        self.sixty_image.resize(int(round(60)),int(round((60))))
