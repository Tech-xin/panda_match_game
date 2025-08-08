from django.db import models
from accounts.models import Player

class Leaderboard(models.Model):
    """
    Leaderboard model to track daily, weekly, and all-time rankings
    """
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('all_time', 'All Time'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    date_recorded = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ['player', 'period', 'date_recorded']
        indexes = [
            models.Index(fields=['period', 'score']),
            models.Index(fields=['date_recorded']),
        ]
    
    def __str__(self):
        return f"{self.player.user.username} - {self.period} - {self.score}"