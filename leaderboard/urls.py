from django.urls import path
from . import views

urlpatterns = [
    path('', views.leaderboard_home, name='leaderboard_home'),
    path('daily/', views.daily_leaderboard, name='daily_leaderboard'),
    path('weekly/', views.weekly_leaderboard, name='weekly_leaderboard'),
    path('all-time/', views.all_time_leaderboard, name='all_time_leaderboard'),
]