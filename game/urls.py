from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_home, name='game_home'),
    path('levels/', views.level_select, name='level_select'),
    path('start/<int:level_id>/', views.start_game, name='start_game'),
    path('play/<int:session_id>/', views.play_game, name='play_game'),
    path('action/<int:session_id>/', views.game_action, name='game_action'),
    path('result/<int:session_id>/', views.game_result, name='game_result'),
    path('abandon/<int:session_id>/', views.abandon_game, name='abandon_game'),
    path('save_time/<int:session_id>/', views.save_game_time, name='save_game_time'),
]
