from django.contrib import admin
from .models import Player

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'level_progress')
    list_filter = ('level_progress',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-score',)