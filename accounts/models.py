from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    """
    Player model extending Django's built-in User model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player')
    score = models.IntegerField(default=0)
    level_progress = models.IntegerField(default=1)
    
    def __str__(self):
        return self.user.username