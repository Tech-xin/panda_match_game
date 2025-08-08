from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .models import Leaderboard
from accounts.models import Player

@login_required
def leaderboard_home(request):
    """
    Display leaderboard options
    """
    return render(request, 'leaderboard/home.html')

@login_required
def daily_leaderboard(request):
    """
    Display daily leaderboard
    """
    # Today's date
    today = timezone.now().date()
    
    # Get top players for today
    top_players = Leaderboard.objects.filter(
        period='daily',
        date_recorded=today
    ).order_by('-score')[:10]
    
    # Get current player's rank if they're on the leaderboard
    player_rank = None
    player_entry = Leaderboard.objects.filter(
        period='daily',
        date_recorded=today,
        player=request.user.player
    ).first()
    
    if player_entry:
        higher_scores = Leaderboard.objects.filter(
            period='daily',
            date_recorded=today,
            score__gt=player_entry.score
        ).count()
        player_rank = higher_scores + 1
    
    context = {
        'leaderboard_type': 'Daily',
        'top_players': top_players,
        'player_rank': player_rank,
        'player_entry': player_entry
    }
    
    return render(request, 'leaderboard/leaderboard.html', context)

@login_required
def weekly_leaderboard(request):
    """
    Display weekly leaderboard
    """
    # Today's date
    today = timezone.now().date()
    
    # Start of current week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    
    # Get top players for this week
    top_players = Leaderboard.objects.filter(
        period='weekly',
        date_recorded__gte=start_of_week,
        date_recorded__lte=today
    ).order_by('-score')[:10]
    
    # Get current player's rank if they're on the leaderboard
    player_rank = None
    player_entry = Leaderboard.objects.filter(
        period='weekly',
        date_recorded__gte=start_of_week,
        date_recorded__lte=today,
        player=request.user.player
    ).first()
    
    if player_entry:
        higher_scores = Leaderboard.objects.filter(
            period='weekly',
            date_recorded__gte=start_of_week,
            date_recorded__lte=today,
            score__gt=player_entry.score
        ).count()
        player_rank = higher_scores + 1
    
    context = {
        'leaderboard_type': 'Weekly',
        'top_players': top_players,
        'player_rank': player_rank,
        'player_entry': player_entry
    }
    
    return render(request, 'leaderboard/leaderboard.html', context)

@login_required
def all_time_leaderboard(request):
    """
    Display all-time leaderboard
    """
    # Get top players of all time
    top_players = Leaderboard.objects.filter(
        period='all_time'
    ).order_by('-score')[:10]
    
    # Get current player's rank if they're on the leaderboard
    player_rank = None
    player_entry = Leaderboard.objects.filter(
        period='all_time',
        player=request.user.player
    ).first()
    
    if player_entry:
        higher_scores = Leaderboard.objects.filter(
            period='all_time',
            score__gt=player_entry.score
        ).count()
        player_rank = higher_scores + 1
    
    context = {
        'leaderboard_type': 'All Time',
        'top_players': top_players,
        'player_rank': player_rank,
        'player_entry': player_entry
    }
    
    return render(request, 'leaderboard/leaderboard.html', context)

def update_leaderboards(player, score):
    """
    Update leaderboards with player's score
    """
    today = timezone.now().date()
    
    # Update daily leaderboard
    daily_entry, created = Leaderboard.objects.get_or_create(
        player=player,
        period='daily',
        date_recorded=today,
        defaults={'score': score}
    )
    
    if not created and score > daily_entry.score:
        daily_entry.score = score
        daily_entry.save()
    
    # Update weekly leaderboard
    weekly_entry, created = Leaderboard.objects.get_or_create(
        player=player,
        period='weekly',
        date_recorded=today,
        defaults={'score': score}
    )
    
    if not created and score > weekly_entry.score:
        weekly_entry.score = score
        weekly_entry.save()
    
    # Update all-time leaderboard
    all_time_entry, created = Leaderboard.objects.get_or_create(
        player=player,
        period='all_time',
        defaults={'score': score, 'date_recorded': today}
    )
    
    if not created and score > all_time_entry.score:
        all_time_entry.score = score
        all_time_entry.date_recorded = today
        all_time_entry.save()