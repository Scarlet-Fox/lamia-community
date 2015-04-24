from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from . import models
from . import forms

def index(request):
    context = {}
    return render(request, "general/base.jade", context)

@csrf_exempt
def sign_out(request):
    if request.method == "POST":
        logout(request)
        return redirect("/")

class SignInView(FormView):
    template_name = "general/sign_in.jade"
    form_class = forms.SignInForm
    success_url = "/"
    
    def form_valid(self, form):
        login(self.request, form.cleaned_data["authenticated_user"])
        return super(SignInView, self).form_valid(form)

class RegisterView(FormView):
    template_name = "general/registration.jade"
    form_class = forms.RegisterForm
    success_url = "/"
    
    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        u = User.objects.create_user(
            cleaned_data["username"].lower().strip(), 
            cleaned_data["email"], 
            cleaned_data["password"].strip()
        )
        u.save()
        p = models.Profile(
            user = u,
            how_found = cleaned_data["how_did_you_find_us"],
            display_name = cleaned_data["username"].strip()
        )
        p.save()
        # SETUP EMAIL ADDRESS STUFF
        return super(RegisterView, self).form_valid(form)
        
        