from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import json

from .models import Level, GameSession, Tile, Move
from .game_logic import GameBoard
from leaderboard.views import update_leaderboards

@login_required
def game_home(request):
    """
    View for the game home screen
    """
    player = request.user.player
    levels = Level.objects.all()
    
    # Get the player's active game sessions
    active_sessions = GameSession.objects.filter(
        player=player,
        status='active'
    ).order_by('-start_time')
    
    context = {
        'player': player,
        'levels': levels,
        'active_sessions': active_sessions
    }
    
    return render(request, 'game/home.html', context)

@login_required
def level_select(request):
    """
    View for selecting a level
    """
    player = request.user.player
    levels = Level.objects.all()
    
    # Calculate progress for each level
    level_data = []
    for level in levels:
        # Check if level is unlocked
        unlocked = player.level_progress >= level.level_id
        
        # Get best score for this level
        best_score = GameSession.objects.filter(
            player=player,
            level=level,
            status='completed'
        ).order_by('-score').first()
        
        level_data.append({
            'level': level,
            'unlocked': unlocked,
            'best_score': best_score.score if best_score else 0
        })
    
    context = {
        'player': player,
        'level_data': level_data
    }
    
    return render(request, 'game/level_select.html', context)

@login_required
def start_game(request, level_id):
    """
    Start a new game session for the specified level
    """
    player = request.user.player
    level = get_object_or_404(Level, level_id=level_id)
    
    # Check if level is unlocked
    if player.level_progress < level.level_id:
        return redirect('level_select')
    
    # Create new game session
    session = GameSession.objects.create(
        player=player,
        level=level,
        status='active'
    )
    
    # Initialize the game board
    game_board = GameBoard(session)
    game_board.initialize_board()
    
    return redirect('play_game', session_id=session.session_id)

@login_required
def play_game(request, session_id):
    """
    View for the active game board
    """
    player = request.user.player
    session = get_object_or_404(GameSession, session_id=session_id, player=player)
    
    # Check if game is already completed
    if session.status != 'active':
        return redirect('game_result', session_id=session.session_id)
    
    # Load the game board
    game_board = GameBoard(session)
    
    # Get only accessible tiles for rendering
    accessible_tiles = {}
    for key, tile in game_board.board.items():
        x, y, layer = map(int, key.split(','))
        if game_board.is_tile_accessible(x, y, layer):
            accessible_tiles[key] = tile
        
    context = {
        'player': player,
        'session': session,
        'board': game_board.board,  # 传递完整的游戏板数据，用于计算堆叠高度
        'accessible_tiles': accessible_tiles,  # 只有可访问的方块会被渲染
        'buffer': game_board.buffer,
        'removed_tiles': game_board.removed_tiles,
        'level': session.level,
        'difficulty': session.level.difficulty  # 传递难度级别
    }
    
    return render(request, 'game/play.html', context)

@login_required
def game_action(request, session_id):
    """
    Handle game actions via AJAX
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=400)
    
    player = request.user.player
    session = get_object_or_404(GameSession, session_id=session_id, player=player)
    
    # Check if game is already completed
    if session.status != 'active':
        return JsonResponse({'error': 'Game session is not active'}, status=400)
    
    # Load the game board
    game_board = GameBoard(session)
    
    # Parse action from request
    try:
        data = json.loads(request.body)
        action = data.get('action')
    except:
        return JsonResponse({'error': 'Invalid request data'}, status=400)
    
    response = {'success': False}
    
    # Handle different actions
    if action == 'select_tile':
        tile_id = data.get('tile_id')
        
        # 获取选中的方块信息
        try:
            selected_tile = Tile.objects.get(tile_id=tile_id, game_session=session)
            print(f"选中的方块: ID={selected_tile.tile_id}, 位置=({selected_tile.position_x},{selected_tile.position_y},{selected_tile.layer}), 类型={selected_tile.tile_type}")
        except Tile.DoesNotExist:
            print(f"找不到方块: ID={tile_id}")
        
        # 获取选中前的可访问方块
        before_accessible_tiles = {}
        for key, tile in game_board.board.items():
            x, y, layer = map(int, key.split(','))
            if game_board.is_tile_accessible(x, y, layer):
                before_accessible_tiles[key] = tile
        print(f"选中前的可访问方块数量: {len(before_accessible_tiles)}")
        
        success = game_board.select_tile(tile_id)
        
        if success:
            print("View: select_tile success. Buffer:", game_board.buffer)
            game_board.save_buffer_state()
            
            response['success'] = True
            response['buffer'] = game_board.buffer  # 确保返回完整的栅栏数据
            response['score'] = session.score
            response['board'] = game_board.board  # 返回完整的游戏板数据
            
            # 获取更新后的可访问方块
            accessible_tiles = {}
            for key, tile in game_board.board.items():
                x, y, layer = map(int, key.split(','))
                if game_board.is_tile_accessible(x, y, layer):
                    accessible_tiles[key] = tile
            
            print(f"选中后的可访问方块数量: {len(accessible_tiles)}")
            
            # 找出新增的可访问方块
            new_accessible_keys = set(accessible_tiles.keys()) - set(before_accessible_tiles.keys())
            if new_accessible_keys:
                print(f"新增的可访问方块: {len(new_accessible_keys)}")
                for key in new_accessible_keys:
                    tile = accessible_tiles[key]
                    print(f"  新增可访问方块: 位置=({tile['x']},{tile['y']},{tile['layer']}), 类型={tile['type']}")
            
            response['accessible_tiles'] = accessible_tiles
            
            # 检查匹配情况
            if len(game_board.buffer) >= 3:
                # 检查是否已匹配
                response['is_match'] = False  # 初始值为False
                
                # 在check_buffer_matches方法中会检查匹配并更新栅栏
                # 如果有匹配，check_buffer_matches方法会自动处理
            
            # 检查游戏是否结束
            if game_board.is_game_over():
                game_board.complete_level()
                # 更新排行榜
                update_leaderboards(player, session.score)
                response['game_over'] = True
    
    elif action == 'use_remove_tool':
        success = game_board.use_remove_tool()
        
        if success:
            response['success'] = True
            response['buffer'] = game_board.buffer
            response['removed_tiles'] = game_board.removed_tiles
    
    elif action == 'use_withdraw_tool':
        success = game_board.use_withdraw_tool()
        
        if success:
            response['success'] = True
            response['buffer'] = game_board.buffer
            
            # Get updated board and accessible tiles
            response['board'] = game_board.board  # 返回完整的游戏板数据
            
            accessible_tiles = {}
            for key, tile in game_board.board.items():
                x, y, layer = map(int, key.split(','))
                if game_board.is_tile_accessible(x, y, layer):
                    accessible_tiles[key] = tile
            
            response['accessible_tiles'] = accessible_tiles
    
    elif action == 'use_shuffle_tool':
        success = game_board.use_shuffle_tool()
        
        if success:
            response['success'] = True
            
            # Get updated board and accessible tiles
            response['board'] = game_board.board  # 返回完整的游戏板数据
            
            accessible_tiles = {}
            for key, tile in game_board.board.items():
                x, y, layer = map(int, key.split(','))
                if game_board.is_tile_accessible(x, y, layer):
                    accessible_tiles[key] = tile
            
            response['accessible_tiles'] = accessible_tiles
    
    elif action == 'return_removed_tile':
        tile_id = data.get('tile_id')
        success = game_board.return_removed_tile(tile_id)
        
        if success:
            response['success'] = True
            response['buffer'] = game_board.buffer
            response['removed_tiles'] = game_board.removed_tiles
            response['score'] = session.score
            
            # 检查游戏是否结束
            if game_board.is_game_over():
                game_board.complete_level()
                # 更新排行榜
                update_leaderboards(player, session.score)
                response['game_over'] = True
    
    else:
        response['error'] = 'Invalid action'
    
    return JsonResponse(response)

@login_required
def game_result(request, session_id):
    """
    View for game results after completion
    """
    player = request.user.player
    session = get_object_or_404(GameSession, session_id=session_id, player=player)
    
    # If game is still active, mark it as completed
    if session.status == 'active':
        session.status = 'completed'
        session.end_time = timezone.now()
        session.save()
        
        # Update leaderboards with player's score
        update_leaderboards(player, session.score)
    
    # Get statistics
    moves = Move.objects.filter(game_session=session).count()
    duration = (session.end_time - session.start_time).total_seconds() if session.end_time else 0
    
    # Get next level if available
    next_level = None
    if session.level.level_id < player.level_progress:
        try:
            next_level = Level.objects.get(level_id=session.level.level_id + 1)
        except Level.DoesNotExist:
            pass
    
    context = {
        'player': player,
        'session': session,
        'moves': moves,
        'duration': duration,
        'next_level': next_level
    }
    
    return render(request, 'game/result.html', context)

@login_required
def abandon_game(request, session_id):
    """
    Abandon a game session
    """
    player = request.user.player
    session = get_object_or_404(GameSession, session_id=session_id, player=player)
    
    if session.status == 'active':
        session.status = 'abandoned'
        session.end_time = timezone.now()
        session.save()
    
    return redirect('game_home')

@login_required
def save_game_time(request, session_id):
    """
    Save the game time from frontend
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=400)
    
    player = request.user.player
    session = get_object_or_404(GameSession, session_id=session_id, player=player)
    
    try:
        data = json.loads(request.body)
        game_time = data.get('game_time', 0)
        
        if game_time > 0:
            # 计算结束时间
            start_time = session.start_time
            end_time = start_time + timezone.timedelta(seconds=game_time)
            
            # 更新会话
            session.end_time = end_time
            session.save()
            
            return JsonResponse({
                'success': True,
                'game_time': game_time
            })
        else:
            return JsonResponse({'error': 'Invalid game time'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

