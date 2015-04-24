from django import forms
from django.contrib.auth import authenticate
import arrow

class SignInForm(forms.Form):
    username = forms.CharField(label='Username', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email address', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    
    def clean(self):
        cleaned_data = super(SignInForm, self).clean()
        username = cleaned_data.get('username').lower()
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None or cleaned_data.get('email') != "":
            raise forms.ValidationError("Your username or password are incorrect. Try again or email community@worldofequestria.com if you can't login.")
        self.cleaned_data["authenticated_user"] = user
        
class RegisterForm(forms.Form):
    username = forms.CharField(label='Username', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email address', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', max_length=255, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(label='Confirm Password', max_length=255, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    how_did_you_find_us = forms.CharField(label="How did you find us?", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    MANE6 = ["rainbow dash", "twilight sparkle", "tarity", "pinkie pie", "applejack", "fluttershy"]
    name_one_of_the_mane6 = forms.CharField(label="Name one of the Mane 6?", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    birth_month = forms.ChoiceField(choices=[(x,x) for x in range(1, 12)])
    birth_year = forms.ChoiceField(choices=[(x,x) for x in range(1930, 2015)], initial=1991)
    
    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        print cleaned_data
        
        try:        
            if cleaned_data["password"] != cleaned_data["confirm_password"]:
                raise forms.ValidationError("Your passwords do not match.")
        except KeyError:
            pass
            
        try:
            if cleaned_data["name_one_of_the_mane6"].lower().strip() not in self.MANE6:
                raise forms.ValidationError("Name one of the Mane 6 ponies (hint: one rhymes with Clarity).")
        except KeyError:
            pass
        
        birth = arrow.Arrow(int(cleaned_data["birth_year"]), int(cleaned_data["birth_month"]), 1)
        if ((arrow.now()-birth).days+31)/365.0 < 13:
            raise forms.ValidationError("Members under the age of 13 are not allowed, please come back later! :)")
            
        