from django.template import RequestContext
from . import models

def profile_processor(request):
    if request.user.is_authenticated():
        return { "user_profile": models.Profile.objects.filter(user__id=request.user.pk) }
    else:
        return {}