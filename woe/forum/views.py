from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
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
        print "okay"