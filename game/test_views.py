from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Player
from .models import Level, GameSession, Tile, Move
import json
from unittest.mock import patch, MagicMock

class GameViewsTests(TestCase):
    """测试游戏视图函数"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建测试客户端
        self.client = Client()
        
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
        
        # 登录用户
        self.client.login(username='testuser', password='12345')
        
        # 模拟URL反向解析
        self.url_patcher = patch('django.urls.reverse')
        self.mock_reverse = self.url_patcher.start()
        self.mock_reverse.side_effect = self._mock_reverse
        
        # 创建游戏会话
        self.game_session = GameSession.objects.create(
            player=self.player,
            level=self.level
        )
    
    def tearDown(self):
        """清理测试环境"""
        self.url_patcher.stop()
    
    def _mock_reverse(self, viewname, args=None, kwargs=None):
        """模拟URL反向解析"""
        if viewname == 'game_home':
            return '/game/'
        elif viewname == 'start_game':
            return '/game/start/'
        elif viewname == 'play_game':
            return f'/game/play/{args[0]}/'
        elif viewname == 'game_action':
            return f'/game/action/{args[0]}/'
        elif viewname == 'level_select':
            return '/game/levels/'
        elif viewname == 'game_result':
            return f'/game/result/{args[0]}/'
        elif viewname == 'abandon_game':
            return f'/game/abandon/{args[0]}/'
        else:
            return f'/{viewname}/'
    
    @patch('game.views.render')
    def test_game_home_view(self, mock_render):
        """测试游戏主页视图"""
        # 模拟render返回一个HttpResponse对象
        mock_render.return_value = MagicMock(status_code=200)
        
        # 模拟GameSession.objects.filter返回值
        with patch('game.views.GameSession.objects.filter') as mock_filter:
            mock_filter.return_value.order_by.return_value = []
            
            # 调用视图
            from game.views import game_home
            request = MagicMock()
            request.user = self.user
            
            response = game_home(request)
            
            # 验证响应状态码
            self.assertEqual(response.status_code, 200)
            
            # 验证使用了正确的模板
            mock_render.assert_called_once()
            self.assertEqual(mock_render.call_args[0][1], 'game/home.html')
    
    @patch('game.views.redirect')
    @patch('game.views.GameBoard')
    def test_start_game_view(self, mock_game_board, mock_redirect):
        """测试开始游戏视图"""
        # 模拟redirect返回一个HttpResponse对象
        mock_redirect.return_value = MagicMock(status_code=302)
        
        # 调用视图
        from game.views import start_game
        request = MagicMock()
        request.method = 'POST'
        request.POST = {'level_id': self.level.level_id}
        request.user = self.user
        
        response = start_game(request, self.level.level_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 302)
        
        # 验证创建了游戏会话
        self.assertEqual(GameSession.objects.count(), 2)  # 包括setUp中创建的一个
        
        # 验证重定向到游戏页面
        game_session = GameSession.objects.last()
        mock_redirect.assert_called_once()
        mock_redirect.assert_called_with('play_game', session_id=game_session.session_id)
    
    @patch('game.views.render')
    @patch('game.views.GameBoard')
    def test_play_game_view(self, mock_game_board, mock_render):
        """测试游戏页面视图"""
        # 模拟GameBoard实例
        mock_board_instance = MagicMock()
        mock_board_instance.board = {'0,0,0': {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0}}
        mock_board_instance.buffer = []
        mock_board_instance.removed_tiles = []
        mock_board_instance.is_tile_accessible.return_value = True
        mock_game_board.return_value = mock_board_instance
        
        # 模拟render返回一个HttpResponse对象
        mock_render.return_value = MagicMock(status_code=200)
        
        # 调用视图
        from game.views import play_game
        request = MagicMock()
        request.user = self.user
        
        response = play_game(request, self.game_session.session_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证使用了正确的模板
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], 'game/play.html')
        
        # 验证上下文包含游戏会话
        context = mock_render.call_args[0][2]
        self.assertEqual(context['session'], self.game_session)
    
    @patch('game.views.JsonResponse')
    @patch('game.views.GameBoard')
    def test_game_action_select_tile(self, mock_game_board, mock_json_response):
        """测试游戏动作 - 选择方块"""
        # 模拟GameBoard实例
        mock_board_instance = MagicMock()
        mock_board_instance.board = {'0,0,0': {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0}}
        mock_board_instance.buffer = [{'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0}]
        mock_board_instance.removed_tiles = []
        mock_board_instance.select_tile.return_value = True
        mock_board_instance.is_tile_accessible.return_value = True
        mock_board_instance.is_game_over.return_value = False
        mock_game_board.return_value = mock_board_instance
        
        # 模拟JsonResponse返回一个HttpResponse对象
        mock_json_response.return_value = MagicMock(status_code=200)
        
        # 创建方块
        tile = Tile.objects.create(
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 调用视图
        from game.views import game_action
        request = MagicMock()
        request.method = 'POST'
        request.user = self.user
        request.body = json.dumps({
            'action': 'select_tile',
            'tile_id': tile.tile_id
        }).encode('utf-8')
        
        response = game_action(request, self.game_session.session_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        mock_json_response.assert_called_once()
        self.assertTrue(mock_json_response.call_args[0][0]['success'])
    
    @patch('game.views.JsonResponse')
    @patch('game.views.GameBoard')
    def test_game_action_use_remove_tool(self, mock_game_board, mock_json_response):
        """测试游戏动作 - 使用移除工具"""
        # 模拟GameBoard实例
        mock_board_instance = MagicMock()
        mock_board_instance.buffer = []
        mock_board_instance.removed_tiles = [{'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0}]
        mock_board_instance.use_remove_tool.return_value = True
        mock_game_board.return_value = mock_board_instance
        
        # 模拟JsonResponse返回一个HttpResponse对象
        mock_json_response.return_value = MagicMock(status_code=200)
        
        # 调用视图
        from game.views import game_action
        request = MagicMock()
        request.method = 'POST'
        request.user = self.user
        request.body = json.dumps({
            'action': 'use_remove_tool'
        }).encode('utf-8')
        
        response = game_action(request, self.game_session.session_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        mock_json_response.assert_called_once()
        self.assertTrue(mock_json_response.call_args[0][0]['success'])
    
    @patch('game.views.JsonResponse')
    @patch('game.views.GameBoard')
    def test_game_action_return_removed_tile(self, mock_game_board, mock_json_response):
        """测试游戏动作 - 返回移除方块"""
        # 模拟GameBoard实例
        mock_board_instance = MagicMock()
        mock_board_instance.buffer = [{'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0}]
        mock_board_instance.removed_tiles = []
        mock_board_instance.return_removed_tile.return_value = True
        mock_board_instance.is_game_over.return_value = False
        mock_game_board.return_value = mock_board_instance
        
        # 模拟JsonResponse返回一个HttpResponse对象
        mock_json_response.return_value = MagicMock(status_code=200)
        
        # 创建方块
        tile = Tile.objects.create(
            tile_id=1,
            game_session=self.game_session,
            tile_type='bamboo',
            position_x=0,
            position_y=0,
            position_z=0,
            layer=0
        )
        
        # 调用视图
        from game.views import game_action
        request = MagicMock()
        request.method = 'POST'
        request.user = self.user
        request.body = json.dumps({
            'action': 'return_removed_tile',
            'tile_id': 1
        }).encode('utf-8')
        
        response = game_action(request, self.game_session.session_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        mock_json_response.assert_called_once()
        self.assertTrue(mock_json_response.call_args[0][0]['success'])
    
    @patch('game.views.JsonResponse')
    @patch('game.views.GameBoard')
    def test_game_action_get_state(self, mock_game_board, mock_json_response):
        """测试游戏动作 - 获取游戏状态"""
        # 模拟GameBoard实例
        mock_board_instance = MagicMock()
        mock_board_instance.board = {'0,0,0': {'id': 1, 'type': 'bamboo', 'x': 0, 'y': 0, 'layer': 0}}
        mock_board_instance.buffer = []
        mock_board_instance.removed_tiles = []
        mock_game_board.return_value = mock_board_instance
        
        # 模拟JsonResponse返回一个HttpResponse对象
        mock_json_response.return_value = MagicMock(status_code=200)
        
        # 调用视图
        from game.views import game_action
        request = MagicMock()
        request.method = 'POST'
        request.user = self.user
        request.body = json.dumps({
            'action': 'get_state'
        }).encode('utf-8')
        
        response = game_action(request, self.game_session.session_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        mock_json_response.assert_called_once()
        
    @patch('game.views.render')
    def test_game_result_view(self, mock_render):
        """测试游戏结果视图"""
        # 模拟render返回一个HttpResponse对象
        mock_render.return_value = MagicMock(status_code=200)
        
        # 调用视图
        from game.views import game_result
        request = MagicMock()
        request.user = self.user
        
        response = game_result(request, self.game_session.session_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证使用了正确的模板
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], 'game/result.html')
    
    @patch('game.views.redirect')
    def test_abandon_game_view(self, mock_redirect):
        """测试放弃游戏视图"""
        # 模拟redirect返回一个HttpResponse对象
        mock_redirect.return_value = MagicMock(status_code=302)
        
        # 调用视图
        from game.views import abandon_game
        request = MagicMock()
        request.user = self.user
        
        response = abandon_game(request, self.game_session.session_id)
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 302)
        
        # 验证重定向到游戏主页
        mock_redirect.assert_called_once()
        mock_redirect.assert_called_with('game_home') 