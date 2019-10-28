from django.urls import path
from . import views

app_name = 'attendance'
urlpatterns = [
    path('', views.index, name='index'),
    path('users/', views.users, name='users'),
    path('user/<user>/', views.user, name='user'),
    path('collect/', views.collect, name='collect'),
    path('csv/', views.csv, name='csv'),
    path('get/<date>', views.get, name='get'),
]
