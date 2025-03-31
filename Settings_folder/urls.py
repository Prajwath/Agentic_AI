# jingo_django_project/urls.py
from django.contrib import admin
from django.urls import path
from Zingo_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
]