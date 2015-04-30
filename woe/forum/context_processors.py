from django.template import RequestContext
from . import models

def profile_processor(request):
    if request.user.is_authenticated():
        try:
            return { "user_profile": models.Profile.objects.filter(user__id=request.user.pk)[0] }
        except:
            return {}
    else:
        return {}