from django.conf.urls import include, url
from django.contrib import admin
import forum.urls

urlpatterns = [
    # Examples:
    # url(r'^$', 'woe.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', include(forum.urls))
]
