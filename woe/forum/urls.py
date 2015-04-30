from django.conf.urls import url
from forum import views

urlpatterns = [
    url(r'^$', views.Index.as_view()),
    url(r'^sign-in/$', views.SignInView.as_view()),
    url(r'^register/$', views.RegisterView.as_view()),
    url(r'^status/(?P<status>[0-9]+)/$', views.StatusUpdate.as_view()),
    url(r'^member/(?P<profile>[0-9]+)/$', views.UserProfileView.as_view()),
    url(r'^sign-out/$', views.sign_out),
]