from django.shortcuts import render
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login, logout
from . import forms

# Create your views here.
def index(request):
    context = {}
    return render(request, "general/base.jade", context)
    
class SignInView(FormView):
    template_name = "general/sign_in.jade"
    form_class = forms.SignInForm
    success_url = "/"
    
    def form_valid(self, form):
        login(self.request, form.cleaned_data["authenticated_user"])
        return super(SignInView, self).form_valid(form)