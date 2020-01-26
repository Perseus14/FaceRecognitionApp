from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path
from .views import *

app_name = 'api'

urlpatterns = [
    path('login', obtain_auth_token, name='login'),
    path('signup', SignUp.as_view(), name='signup'),
    path('upload', UploadImage.as_view(), name='upload'),
    path('analyze', AnalyzeImage.as_view(), name='analyze'),
]