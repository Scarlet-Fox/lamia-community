from django.shortcuts import render
from scarletsweb import models
from django.http import HttpResponse

def index(request):
    return render(request, 'base.html', {})
