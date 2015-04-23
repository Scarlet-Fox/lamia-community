from django.conf.urls import url
from forum import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^sign-in/$', views.SignInView.as_view(), name='signin'),
]