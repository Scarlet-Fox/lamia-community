import django
django.setup()
import scarletsweb.models as psql
from django.contrib.auth.models import User as SQLUser


#exit()

SQLUser.objects.exclude(username="sallymin").delete()
psql.UserProfile.objects.all().delete()
