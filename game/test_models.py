from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Player
from .models import Level, GameSession, Tile, Move
from django.utils import timezone
from django.db import IntegrityError
import datetime
from django.db import transaction

class LevelModelTests(TestCase):
    """测试Level模型"""
    
    def test_level_creation(self):
        """测试创建关卡"""
        level = Level.objects.create(
            difficulty=2,
            tile_layout=[
                {'type': 'bamboo', 'x': 0, 'y': 0},
                {'type': 'bamboo', 'x': 0, 'y': 1},
                {'type': 'bamboo', 'x': 0, 'y': 2},
            ]
        )
        
        self.assertEqual(level.difficulty, 2)
        self.assertEqual(len(level.tile_layout), 3)
        self.assertEqual(str(level), f"Level {level.level_id} (Difficulty: 2)")
    
    def test_validate_tile_counts(self):
        """测试方块数量验证"""
        # 有效的布局（每种类型的方块数量是3的倍数）
        valid_layout = [
            {'type': 'bamboo', 'x': 0, 'y': 0},
            {'type': 'bamboo', 'x': 0, 'y': 1},
            {'type': 'bamboo', 'x': 0, 'y': 2},
            {'type': 'leaf', 'x': 1, 'y': 0},
            {'type': 'leaf', 'x': 1, 'y': 1},
            {'type': 'leaf', 'x': 1, 'y': 2},
        ]
        
        level = Level(difficulty=1, tile_layout=valid_layout)
        self.assertTrue(level.validate_tile_counts())
        
        # 无效的布局（bamboo只有2个，不是3的倍数）
        invalid_layout = [
            {'type': 'bamboo', 'x': 0, 'y': 0},
            {'type': 'bamboo', 'x': 0, 'y': 1},
            {'type': 'leaf', 'x': 1, 'y': 0},
            {'type': 'leaf', 'x': 1, 'y': 1},
            {'type': 'leaf', 'x': 1, 'y': 2},
        ]
        
        level = Level(difficulty=1, tile_layout=invalid_layout)
        with self.assertRaises(ValueError):
            level.validate_tile_counts()

class GameSessionModelTests(TestCase):
    """测试GameSession模型"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建用户和玩家
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.player = Player.objects.create(user=self.user)
        
        # 创建关卡
        self.level = Level.objects.create(
            difficulty=1,
            tile_layout=[
                {'type': 'bamboo', 'x': 0, 'y': 0},
                {'type': 'bamboo', 'x': 0, 'y': 1},
                {'type': 'bamboo', 'x': 0, 'y': 2},
            ]
        )
    
    def test_game_session_creation(self):
        """测试创建游戏会话"""
        game_session = GameSession.objects.create(
            player=self.player,
            level=self.level,
            score=100,
            status='active'
        )
        
        self.assertEqual(game_session.player, self.player)
        self.assertEqual(game_session.level, self.level)
        self.assertEqual(game_session.score, 100)
        self.assertEqual(game_session.status, 'active')
        self.assertEqual(len(game_session.buffer), 0)
        self.assertEqual(len(game_session.removed_tiles), 0)
        self.assertIsNotNone(game_session.start_time)
        self.assertIsNone(game_session.end_time)
        self.assertEqual(str(game_session), f"Session {game_session.session_id} - {self.user.username}")
    
    def test_game_session_buffer(self):
        """测试游戏会话缓冲区"""
        game_session = GameSession.objects.create(
            player=self.player,
            level=self.level
        )
        
        # 设置缓冲区
        buffer_data = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
            {'id': 2, 'type': 'leaf', 'x': 1, 'y': 0, 'layer': 0},
        ]
        game_session.buffer = buffer_data
        game_session.save()
        
        # 重新加载游戏会话
        game_session = GameSession.objects.get(pk=game_session.session_id)
        
        # 验证缓冲区数据
        self.assertEqual(len(game_session.buffer), 2)
        self.assertEqual(game_session.buffer[0]['id'], 1)
        self.assertEqual(game_session.buffer[0]['type'], 'bamboo')
        self.assertEqual(game_session.buffer[1]['id'], 2)
        self.assertEqual(game_session.buffer[1]['type'], 'leaf')
    
    def test_game_session_removed_tiles(self):
        """测试游戏会话移除的方块"""
        game_session = GameSession.objects.create(
            player=self.player,
            level=self.level
        )
        
        # 设置移除的方块
        removed_tiles = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
        ]
        game_session.removed_tiles = removed_tiles
        game_session.save()
        
        # 重新加载游戏会话
        game_session = GameSession.objects.get(pk=game_session.session_id)
        
        # 验证移除的方块数据
        self.assertEqual(len(game_session.removed_tiles), 1)
        self.assertEqual(game_session.removed_tiles[0]['id'], 1)
        self.assertEqual(game_session.removed_tiles[0]['type'], 'bamboo')

class TileModelTests(TestCase):
    """测试方块模型"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建用户和玩家
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.player = Player.objects.create(user=self.user)
        
        # 创建关卡
        self.level = Level.objects.create(
            difficulty=1,
            tile_layout=[
                {'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
                {'type': 'bamboo', 'x': 0, 'y': 1, 'layer': 0},
                {'type': 'bamboo', 'x': 0, 'y': 2, 'layer': 0},
            ]
        )
        
        # 创建游戏会话
        self.game_session = GameSession.objects.create(
            player=self.player,
            level=self.level
        )
    
    def test_tile_creation(self):
        """测试创建方块"""
        tile = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        self.assertEqual(tile.game_session, self.game_session)
        self.assertEqual(tile.tile_type, 'bamboo')
        self.assertEqual(tile.position_x, 0)
        self.assertEqual(tile.position_y, 0)
        self.assertEqual(tile.position_z, 0)
        self.assertEqual(tile.layer, 0)
    
    def test_tile_unique_constraint(self):
        """测试方块唯一约束"""
        # 创建第一个方块
        Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 尝试创建具有相同位置的第二个方块，应该引发IntegrityError
        with self.assertRaises(IntegrityError):
            # 在新的事务中创建第二个方块
            with transaction.atomic():
                Tile.objects.create(
                    game_session=self.game_session,
                    tile_type='leaf',
                    position_x=0,
                    position_y=0,
                    position_z=0,
                    layer=0
                )
        
        # 创建具有不同位置的第二个方块，应该成功
        tile2 = Tile.objects.create(
            game_session=self.game_session,
            tile_type='leaf',
            position_x=1,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        self.assertEqual(tile2.game_session, self.game_session)
        self.assertEqual(tile2.tile_type, 'leaf')
        self.assertEqual(tile2.position_x, 1)
        self.assertEqual(tile2.position_y, 0)
        self.assertEqual(tile2.position_z, 0)
        self.assertEqual(tile2.layer, 0)

class MoveModelTests(TestCase):
    """测试Move模型"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建用户和玩家
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.player = Player.objects.create(user=self.user)
        
        # 创建关卡
        self.level = Level.objects.create(
            difficulty=1,
            tile_layout=[
                {'type': 'bamboo', 'x': 0, 'y': 0},
                {'type': 'bamboo', 'x': 0, 'y': 1},
                {'type': 'bamboo', 'x': 0, 'y': 2},
            ]
        )
        
        # 创建游戏会话
        self.game_session = GameSession.objects.create(
            player=self.player,
            level=self.level
        )
        
        # 创建方块
        self.tile = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
    
    def test_move_creation_with_tile(self):
        """测试创建带有方块的移动"""
        move = Move.objects.create(
            game_session=self.game_session,
            tile=self.tile,
            action='select'
        )
        
        self.assertEqual(move.game_session, self.game_session)
        self.assertEqual(move.tile, self.tile)
        self.assertEqual(move.action, 'select')
        self.assertIsNotNone(move.move_time)
        self.assertEqual(str(move), f"Move {move.move_id} - select")
    
    def test_move_creation_without_tile(self):
        """测试创建不带方块的移动"""
        move = Move.objects.create(
            game_session=self.game_session,
            action='match'
        )
        
        self.assertEqual(move.game_session, self.game_session)
        self.assertIsNone(move.tile)
        self.assertEqual(move.action, 'match')
        self.assertIsNotNone(move.move_time)
        self.assertEqual(str(move), f"Move {move.move_id} - match")
    
    def test_move_time_auto_now(self):
        """测试移动时间自动设置"""
        # 创建移动
        move = Move.objects.create(
            game_session=self.game_session,
            action='select'
        )
        
        # 验证移动时间在当前时间附近
        now = timezone.now()
        self.assertLess((now - move.move_time).total_seconds(), 10)  # 10秒内 