from django.urls import path
from . import views

app_name = 'attendance'
urlpatterns = [
    path('', views.index, name='index'),
    path('user/<user>/', views.user, name='user'),
    path('collect/', views.collect, name='collect'),
    path('csv/', views.csv, name='csv'),
]
