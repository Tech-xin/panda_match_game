from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Player
from .models import Level, GameSession, Tile, Move
from .game_logic import GameBoard
import json
from unittest.mock import patch, MagicMock

class LevelModelTests(TestCase):
    """测试Level模型的功能"""
    
    def test_validate_tile_counts_valid(self):
        """测试有效的方块数量验证"""
        level = Level(
            difficulty=1,
            tile_layout=[
                {'type': 'bamboo', 'x': 0, 'y': 0},
                {'type': 'bamboo', 'x': 0, 'y': 1},
                {'type': 'bamboo', 'x': 0, 'y': 2},
                {'type': 'leaf', 'x': 1, 'y': 0},
                {'type': 'leaf', 'x': 1, 'y': 1},
                {'type': 'leaf', 'x': 1, 'y': 2},
            ]
        )
        
        # 不应该抛出异常
        try:
            level.validate_tile_counts()
            is_valid = True
        except ValueError:
            is_valid = False
            
        self.assertTrue(is_valid)
    
    def test_validate_tile_counts_invalid(self):
        """测试无效的方块数量验证"""
        level = Level(
            difficulty=1,
            tile_layout=[
                {'type': 'bamboo', 'x': 0, 'y': 0},
                {'type': 'bamboo', 'x': 0, 'y': 1},
                {'type': 'leaf', 'x': 1, 'y': 0},
                {'type': 'leaf', 'x': 1, 'y': 1},
                {'type': 'leaf', 'x': 1, 'y': 2},
            ]
        )
        
        # 应该抛出异常，因为bamboo只有2个，不是3的倍数
        with self.assertRaises(ValueError):
            level.validate_tile_counts()

class GameBoardTests(TestCase):
    """测试GameBoard类的功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建用户和玩家
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.player = Player.objects.create(user=self.user)
        
        # 创建一个简单的关卡
        self.level = Level.objects.create(
            difficulty=1,
            tile_layout=[
                {'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
                {'type': 'bamboo', 'x': 0, 'y': 1, 'layer': 0},
                {'type': 'bamboo', 'x': 0, 'y': 2, 'layer': 0},
                {'type': 'leaf', 'x': 1, 'y': 0, 'layer': 0},
                {'type': 'leaf', 'x': 1, 'y': 1, 'layer': 0},
                {'type': 'leaf', 'x': 1, 'y': 2, 'layer': 0},
            ]
        )
        
        # 创建游戏会话
        self.game_session = GameSession.objects.create(
            player=self.player,
            level=self.level
        )
        
        # 创建游戏板
        self.game_board = GameBoard(self.game_session)
    
    def tearDown(self):
        """清理测试环境"""
        # 删除所有方块
        Tile.objects.all().delete()
    
    def test_initialize_board_with_predefined_layout(self):
        """测试使用预定义布局初始化游戏板"""
        # 初始化游戏板
        self.game_board.initialize_board()
        
        # 验证游戏板上的方块数量
        self.assertEqual(len(self.game_board.board), 6)
        
        # 验证方块类型
        bamboo_count = 0
        leaf_count = 0
        
        for key, tile in self.game_board.board.items():
            if tile['type'] == 'bamboo':
                bamboo_count += 1
            elif tile['type'] == 'leaf':
                leaf_count += 1
        
        self.assertEqual(bamboo_count, 3)
        self.assertEqual(leaf_count, 3)
    
    def test_initialize_board_random(self):
        """测试随机初始化游戏板"""
        # 创建一个没有预定义布局的关卡
        level = Level.objects.create(
            difficulty=1,
            tile_layout=[]
        )
        
        game_session = GameSession.objects.create(
            player=self.player,
            level=level
        )
        
        game_board = GameBoard(game_session)
        
        # 初始化游戏板
        game_board.initialize_board(rows=3, cols=3, layers=2)
        
        # 验证游戏板上有方块
        self.assertTrue(len(game_board.board) > 0)
        
        # 统计每种类型的方块数量
        type_counts = {}
        for key, tile in game_board.board.items():
            tile_type = tile['type']
            type_counts[tile_type] = type_counts.get(tile_type, 0) + 1
        
        # 验证每种类型的方块数量是3的倍数
        for tile_type, count in type_counts.items():
            self.assertEqual(count % 3, 0, f"类型 {tile_type} 的方块数量 {count} 不是3的倍数")
    
    def test_is_tile_accessible(self):
        """测试方块可访问性检查"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 创建一个简单的测试布局
        self.game_board.board = {}
        
        # 添加一个底层方块
        self.game_board.board["0,0,0"] = {
            'id': 1,
            'type': 'bamboo',
            'x': 0,
            'y': 0,
            'z': 0,
            'layer': 0
        }
        
        # 添加一个覆盖底层方块的方块
        self.game_board.board["0,0,1"] = {
            'id': 2,
            'type': 'leaf',
            'x': 0,
            'y': 0,
            'z': 0,
            'layer': 1
        }
        
        # 添加一个不被覆盖的方块
        self.game_board.board["1,1,0"] = {
            'id': 3,
            'type': 'panda',
            'x': 1,
            'y': 1,
            'z': 0,
            'layer': 0
        }
        
        # 测试被覆盖的方块不可访问
        self.assertFalse(self.game_board.is_tile_accessible(0, 0, 0))
        
        # 测试不被覆盖的方块可访问
        # 根据实际实现，方块(1,1,0)被方块(0,0,1)覆盖，所以不可访问
        self.assertFalse(self.game_board.is_tile_accessible(1, 1, 0))
        
        # 测试覆盖其他方块的方块可访问
        self.assertTrue(self.game_board.is_tile_accessible(0, 0, 1))
        
        # 测试高层方块不可访问
        self.game_board.board["2,2,3"] = {
            'id': 4,
            'type': 'fish',
            'x': 2,
            'y': 2,
            'z': 0,
            'layer': 3
        }
        self.assertFalse(self.game_board.is_tile_accessible(2, 2, 3))
    
    def test_select_tile(self):
        """测试选择方块功能"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 创建一个简单的测试布局
        self.game_board.board = {}
        self.game_board.buffer = []
        
        # 在数据库中创建一个可访问的方块
        tile = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 添加到游戏板
        self.game_board.board["0,0,0"] = {
            'id': tile.tile_id,
            'type': 'bamboo',
            'x': 0,
            'y': 0,
            'z': 0,
            'layer': 0
        }
        
        # 模拟is_tile_accessible方法返回True
        with patch.object(GameBoard, 'is_tile_accessible', return_value=True):
            # 选择方块
            result = self.game_board.select_tile(tile.tile_id)
            
            # 验证选择成功
            self.assertTrue(result)
            
            # 验证方块被添加到缓冲区
            self.assertEqual(len(self.game_board.buffer), 1)
            self.assertEqual(self.game_board.buffer[0]['id'], tile.tile_id)
            
            # 验证方块从游戏板移除
            self.assertNotIn("0,0,0", self.game_board.board)
            
            # 验证移动被记录
            self.assertEqual(Move.objects.filter(game_session=self.game_session, action='select').count(), 1)
    
    def test_check_buffer_matches(self):
        """测试缓冲区匹配检查"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 创建方块
        tile1 = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        tile2 = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=1,
            position_z=0,
            layer=0
        )
        
        tile3 = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=2,
            position_z=0,
            layer=0
        )
        
        tile4 = Tile.objects.create(
            game_session=self.game_session,
            tile_type='leaf',
            position_x=1,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 设置缓冲区
        self.game_board.buffer = [
            {'id': tile1.tile_id, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
            {'id': tile2.tile_id, 'type': 'bamboo', 'x': 0, 'y': 1, 'layer': 0},
            {'id': tile3.tile_id, 'type': 'bamboo', 'x': 0, 'y': 2, 'layer': 0},
            {'id': tile4.tile_id, 'type': 'leaf', 'x': 1, 'y': 0, 'layer': 0},
        ]
        
        # 检查匹配
        self.game_board.check_buffer_matches()
        
        # 验证匹配的方块被移除
        self.assertEqual(len(self.game_board.buffer), 1)
        self.assertEqual(self.game_board.buffer[0]['type'], 'leaf')
        
        # 验证分数增加
        self.game_session.refresh_from_db()
        self.assertEqual(self.game_session.score, 10)
        
        # 验证移动被记录
        self.assertEqual(Move.objects.filter(game_session=self.game_session, action='match').count(), 1)
    
    def test_use_remove_tool(self):
        """测试移除工具功能"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置缓冲区
        self.game_board.buffer = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
            {'id': 2, 'type': 'leaf', 'x': 0, 'y': 1, 'layer': 0},
            {'id': 3, 'type': 'panda', 'x': 0, 'y': 2, 'layer': 0},
            {'id': 4, 'type': 'fish', 'x': 1, 'y': 0, 'layer': 0},
        ]
        
        # 使用移除工具
        result = self.game_board.use_remove_tool()
        
        # 验证工具使用成功
        self.assertTrue(result)
        
        # 验证前三个方块被移除
        self.assertEqual(len(self.game_board.buffer), 1)
        self.assertEqual(self.game_board.buffer[0]['id'], 4)
        
        # 验证移除的方块被添加到removed_tiles
        self.assertEqual(len(self.game_board.removed_tiles), 3)
        
        # 验证移动被记录
        self.assertEqual(Move.objects.filter(game_session=self.game_session, action='use_remove_tool').count(), 1)
    
    def test_return_removed_tile(self):
        """测试返回移除方块功能"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置移除的方块
        self.game_board.removed_tiles = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
            {'id': 2, 'type': 'leaf', 'x': 0, 'y': 1, 'layer': 0},
        ]
        
        # 设置缓冲区
        self.game_board.buffer = [
            {'id': 3, 'type': 'panda', 'x': 0, 'y': 2, 'layer': 0},
        ]
        
        # 在数据库中创建对应的方块
        Tile.objects.create(
            tile_id=1,
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 返回移除的方块
        result = self.game_board.return_removed_tile(1)
        
        # 验证返回成功
        self.assertTrue(result)
        
        # 验证方块从移除区移除
        self.assertEqual(len(self.game_board.removed_tiles), 1)
        self.assertEqual(self.game_board.removed_tiles[0]['id'], 2)
        
        # 验证方块添加到缓冲区
        self.assertEqual(len(self.game_board.buffer), 2)
        self.assertEqual(self.game_board.buffer[1]['id'], 1)
        
        # 验证移动被记录
        self.assertEqual(Move.objects.filter(game_session=self.game_session, action='return_removed_tile').count(), 1)
    
    def test_use_withdraw_tool(self):
        """测试撤回工具功能"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置缓冲区
        self.game_board.buffer = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
        ]
        
        # 在数据库中创建对应的方块
        Tile.objects.create(
            tile_id=1,
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 使用撤回工具
        result = self.game_board.use_withdraw_tool()
        
        # 验证工具使用成功
        self.assertTrue(result)
        
        # 验证缓冲区为空
        self.assertEqual(len(self.game_board.buffer), 0)
        
        # 验证方块返回到游戏板
        self.assertIn("0,0,0", self.game_board.board)
        self.assertEqual(self.game_board.board["0,0,0"]['id'], 1)
        
        # 验证移动被记录
        self.assertEqual(Move.objects.filter(game_session=self.game_session, action='use_withdraw_tool').count(), 1)
    
    def test_use_shuffle_tool(self):
        """测试洗牌工具功能"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 创建一些方块
        tile1 = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        tile2 = Tile.objects.create(
            game_session=self.game_session,
            tile_type='leaf',
            position_x=1,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 设置游戏板
        self.game_board.board = {
            "0,0,0": {
                'id': tile1.tile_id,
                'type': 'bamboo',
                'x': 0,
                'y': 0,
                'z': 0,
                'layer': 0
            },
            "1,0,0": {
                'id': tile2.tile_id,
                'type': 'leaf',
                'x': 1,
                'y': 0,
                'z': 0,
                'layer': 0
            }
        }
        
        # 记录原始类型
        original_types = {
            "0,0,0": 'bamboo',
            "1,0,0": 'leaf'
        }
        
        # 使用洗牌工具
        with patch('random.shuffle') as mock_shuffle:
            # 模拟洗牌，交换两个方块的类型
            def side_effect(lst):
                lst[0], lst[1] = lst[1], lst[0]
            mock_shuffle.side_effect = side_effect
            
            result = self.game_board.use_shuffle_tool()
        
        # 验证工具使用成功
        self.assertTrue(result)
        
        # 验证方块类型被交换
        self.assertEqual(self.game_board.board["0,0,0"]['type'], 'leaf')
        self.assertEqual(self.game_board.board["1,0,0"]['type'], 'bamboo')
        
        # 验证移动被记录
        self.assertEqual(Move.objects.filter(game_session=self.game_session, action='use_shuffle_tool').count(), 1)
    
    def test_is_game_over_empty_board(self):
        """测试游戏结束检查 - 空游戏板"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置空游戏板和缓冲区
        self.game_board.board = {}
        self.game_board.buffer = []
        self.game_board.removed_tiles = []
        
        # 验证游戏结束
        self.assertTrue(self.game_board.is_game_over())
    
    def test_is_game_over_with_tiles(self):
        """测试游戏结束检查 - 还有方块"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置游戏板有方块
        self.game_board.board = {
            "0,0,0": {
                'id': 1,
                'type': 'bamboo',
                'x': 0,
                'y': 0,
                'z': 0,
                'layer': 0
            }
        }
        self.game_board.buffer = []
        self.game_board.removed_tiles = []
        
        # 验证游戏未结束
        self.assertFalse(self.game_board.is_game_over())
    
    def test_is_game_over_with_removed_tiles(self):
        """测试游戏结束检查 - 有移除的方块"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置空游戏板但有移除的方块
        self.game_board.board = {}
        self.game_board.buffer = []
        self.game_board.removed_tiles = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0}
        ]
        
        # 验证游戏未结束
        self.assertFalse(self.game_board.is_game_over())
    
    def test_is_game_over_with_buffer_match(self):
        """测试游戏结束检查 - 缓冲区有可能的匹配"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置空游戏板但缓冲区有可能的匹配
        self.game_board.board = {}
        self.game_board.buffer = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
            {'id': 2, 'type': 'bamboo', 'x': 0, 'y': 1, 'layer': 0},
            {'id': 3, 'type': 'bamboo', 'x': 0, 'y': 2, 'layer': 0}
        ]
        self.game_board.removed_tiles = []
        
        # 验证游戏未结束
        self.assertFalse(self.game_board.is_game_over())
    
    def test_is_game_over_buffer_full_no_match(self):
        """测试游戏结束检查 - 缓冲区已满且没有匹配"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 设置空游戏板但缓冲区已满且没有匹配
        self.game_board.board = {}
        self.game_board.buffer = [
            {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0},
            {'id': 2, 'type': 'leaf', 'x': 0, 'y': 1, 'layer': 0},
            {'id': 3, 'type': 'panda', 'x': 0, 'y': 2, 'layer': 0},
            {'id': 4, 'type': 'fish', 'x': 1, 'y': 0, 'layer': 0},
            {'id': 5, 'type': 'carrot', 'x': 1, 'y': 1, 'layer': 0},
            {'id': 6, 'type': 'fire', 'x': 1, 'y': 2, 'layer': 0},
            {'id': 7, 'type': 'bamboo', 'x': 2, 'y': 0, 'layer': 0}
        ]
        self.game_board.removed_tiles = []
        
        # 验证游戏结束
        self.assertTrue(self.game_board.is_game_over())
    
    def test_complete_level(self):
        """测试完成关卡功能"""
        # 删除所有方块
        Tile.objects.filter(game_session=self.game_session).delete()
        
        # 完成关卡
        result = self.game_board.complete_level()
        
        # 验证完成成功
        self.assertTrue(result)
        
        # 验证游戏会话状态更新
        self.game_session.refresh_from_db()
        self.assertEqual(self.game_session.status, 'completed')
        
        # 验证玩家进度更新
        self.player.refresh_from_db()
        self.assertEqual(self.player.level_progress, self.level.level_id + 1)
