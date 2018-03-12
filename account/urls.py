from django.conf.urls import url
from . import views

app_name = "account"

urlpatterns = [
       url(r'^home/', views.home_page, name='home_page'),
       url(r'^login/', views.user_login, name='login_url'),
       url(r'^signup/', views.user_signup, name='signup_url'),
       url(r'^logout/', views.user_logout, name='logout_url'),
       url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activate, name='activate'),
       url(r'^forgot_password/', views.forgot_password, name='forgot_password'),
       url(r'^reset_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.reset_password, name='reset_password'),
       url(r'^prompt1/', views.prompt1, name='prompt1'),
       url(r'^prompt2/', views.prompt2, name='prompt2'),
]
