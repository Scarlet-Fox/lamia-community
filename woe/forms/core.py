from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators
from woe.models.core import User
from flask_wtf.file import FileField, FileAllowed, FileRequired
from PIL import Image

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
        