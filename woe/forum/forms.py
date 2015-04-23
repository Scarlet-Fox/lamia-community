from django import forms
from django.contrib.auth import authenticate

class SignInForm(forms.Form):
    username = forms.CharField(label='Username', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(label='Email address', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    
    def clean(self):
        cleaned_data = super(SignInForm, self).clean()
        username = cleaned_data.get('username').lower()
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None or cleaned_data.get('email') != "":
            raise forms.ValidationError("Your username or password are incorrect. Try again or email community@worldofequestria.com if you can't login.")
        self.cleaned_data["authenticated_user"] = user