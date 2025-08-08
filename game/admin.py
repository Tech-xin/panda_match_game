from django.contrib import admin
from .models import Level, GameSession, Tile, Move

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('level_id', 'difficulty')
    search_fields = ('level_id',)
    ordering = ('level_id',)

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'player', 'level', 'start_time', 'end_time', 'status', 'score')
    list_filter = ('status', 'level')
    search_fields = ('player__user__username',)
    date_hierarchy = 'start_time'
    ordering = ('-start_time',)

@admin.register(Tile)
class TileAdmin(admin.ModelAdmin):
    list_display = ('tile_id', 'game_session', 'tile_type', 'position_x', 'position_y', 'position_z')
    list_filter = ('tile_type',)
    search_fields = ('game_session__player__user__username',)

@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('move_id', 'game_session', 'action', 'move_time')
    list_filter = ('action',)
    search_fields = ('game_session__player__user__username',)
    date_hierarchy = 'move_time'
    ordering = ('-move_time',)