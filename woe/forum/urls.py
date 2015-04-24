from django.conf.urls import url
from forum import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^sign-in/$', views.SignInView.as_view()),
    url(r'^register/$', views.RegisterView.as_view()),
    url(r'^sign-out/$', views.sign_out),
]