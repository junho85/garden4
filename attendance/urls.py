from django.urls import path
from . import views

app_name = 'attendance'
urlpatterns = [
    path('', views.index, name='index'),
    path('users/', views.users, name='users'),
    path('users/<user>/', views.user, name='user'),
    path('api/users/<user>/', views.user_api, name='user'),
    path('collect/', views.collect, name='collect'), # slack_messages 수집
    path('csv/', views.csv, name='csv'),
    path('get/<date>', views.get, name='get'), # 특정일의 출석부 조회. 날짜기준
    path('gets', views.gets, name='get'), # 전체 출석부 조회. 리스트. 유저별.
]
