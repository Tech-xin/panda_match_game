from django.contrib import admin
from .models import Leaderboard

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('player', 'score', 'period', 'date_recorded')
    list_filter = ('period', 'date_recorded')
    search_fields = ('player__user__username',)
    date_hierarchy = 'date_recorded'
    ordering = ('-score',)