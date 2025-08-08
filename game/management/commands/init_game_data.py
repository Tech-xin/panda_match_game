import json
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Player
from game.models import Level
from leaderboard.models import Leaderboard
from django.utils import timezone

class Command(BaseCommand):
    help = 'Initialize the game with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Initializing game data...')
        
        try:
            # Create levels
            self.create_levels()
            
            # Create sample admin user if it doesn't exist
            if not User.objects.filter(username='admin').exists():
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='adminpassword'
                )
                Player.objects.create(user=admin_user, score=0, level_progress=1)
                self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))
            
            self.stdout.write(self.style.SUCCESS('Game data initialized successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error initializing game data: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
    
    def create_levels(self):
        """Create game levels"""
        # Check if levels already exist
        if Level.objects.exists():
            self.stdout.write('Levels already exist, skipping...')
            return
        
        # Create 10 levels with increasing difficulty
        for i in range(1, 11):
            # Generate a tile layout based on level difficulty
            tile_layout = self.generate_tile_layout(i)
            
            Level.objects.create(
                level_id=i,
                difficulty=min(5, (i + 1) // 2),  # Difficulty from 1-5
                tile_layout=tile_layout
            )
            
            self.stdout.write(f'Created Level {i}')
    
    def generate_tile_layout(self, level):
        """Generate a tile layout for a level"""
        # Define board size based on level
        rows = min(8, 4 + level // 2)
        cols = min(8, 4 + level // 2)
        
        # 根据关卡等级确定堆叠层数
        max_layers = min(8, 2 + level // 2)  # 随着关卡提升增加层数，最多8层
        
        # Available tile types
        tile_types = ['bamboo', 'leaf', 'panda', 'fish', 'carrot', 'fire']
        
        # 确定要使用的方块类型数量
        # 确保每个关卡至少使用4种方块类型，最多使用所有6种
        num_types_to_use = min(len(tile_types), max(4, level // 2 + 2))
        active_types = tile_types[:num_types_to_use]
        
        self.stdout.write(f"Level {level} - 使用的方块类型: {', '.join(active_types)}")
        self.stdout.write(f"Level {level} - 棋盘大小: {rows}x{cols}, 最大层数: {max_layers}")
        
        # 计算总可用位置数
        total_positions = rows * cols * max_layers
        self.stdout.write(f"初始总位置数: {total_positions}")
        
        # 确保总位置数是3的倍数
        if total_positions % 3 != 0:
            # 截断到最近的3的倍数
            needed_positions = (total_positions // 3) * 3
            total_positions = needed_positions
        else:
            needed_positions = total_positions
            
        self.stdout.write(f"调整后的位置数: {needed_positions}")
        
        # 创建所有可能的位置
        all_positions = []
        for layer in range(max_layers):
            for y in range(rows):
                for x in range(cols):
                    all_positions.append((x, y, layer))
        
        # 如果位置太多，截断到需要的数量
        if len(all_positions) > needed_positions:
            all_positions = all_positions[:needed_positions]
        
        self.stdout.write(f"截断后的位置数: {len(all_positions)}")
        
        # 计算每种类型的方块应该有多少个
        # 确保每种类型的方块数量都是3的倍数
        
        # 初始化每种类型的方块数量为0
        type_counts = {t: 0 for t in active_types}
        
        # 计算每种类型至少应该有多少个方块（确保是3的倍数）
        base_count_per_type = (needed_positions // len(active_types)) // 3 * 3
        remaining_positions = needed_positions - (base_count_per_type * len(active_types))
        
        self.stdout.write(f"每种类型基础方块数: {base_count_per_type}")
        self.stdout.write(f"剩余位置数: {remaining_positions}")
        
        # 为每种类型分配基础数量的方块
        for tile_type in active_types:
            type_counts[tile_type] = base_count_per_type
        
        # 分配剩余的位置（确保每次分配3个，保持3的倍数）
        remaining_types = list(active_types)
        while remaining_positions >= 3:
            # 随机选择一种类型
            if not remaining_types:
                remaining_types = list(active_types)
            tile_type = random.choice(remaining_types)
            remaining_types.remove(tile_type)
            
            # 为这种类型增加3个方块
            type_counts[tile_type] += 3
            remaining_positions -= 3
        
        # 输出每种类型的分配情况
        for tile_type in active_types:
            triplets = type_counts[tile_type] // 3
            self.stdout.write(f"类型 {tile_type} 分配了 {triplets} 个三元组，共 {type_counts[tile_type]} 个方块")
        
        # 确认总方块数等于需要的位置数
        total_tiles = sum(type_counts.values())
        self.stdout.write(f"总方块数: {total_tiles}, 需要的位置数: {needed_positions}")
        
        if total_tiles != needed_positions:
            raise ValueError(f"分配错误: 总方块数 {total_tiles} 不等于需要的位置数 {needed_positions}")
        
        # 验证每种类型的方块数量是否是3的倍数
        for tile_type, count in type_counts.items():
            if count % 3 != 0:
                raise ValueError(f"分配错误: 类型 {tile_type} 的方块数 {count} 不是3的倍数")
            self.stdout.write(f"验证通过: 类型 {tile_type} 的方块数 {count} 是3的倍数")
        
        # 随机打乱位置
        random.shuffle(all_positions)
        
        # 生成实际的布局
        layout = []
        
        # 创建所有方块类型的列表
        all_tiles = []
        for tile_type, count in type_counts.items():
            all_tiles.extend([tile_type] * count)
        
        # 打乱方块类型
        random.shuffle(all_tiles)
        
        # 放置方块到布局中
        for i, pos in enumerate(all_positions):
            if i >= len(all_tiles):
                break
                
            tile_type = all_tiles[i]
            
            layout.append({
                'x': pos[0],
                'y': pos[1],
                'z': pos[2],
                'layer': pos[2],  # 使用z作为layer
                'type': tile_type
            })
        
        # 最终验证：确保每种类型的方块数量是3的倍数
        final_counts = {}
        for tile in layout:
            tile_type = tile['type']
            final_counts[tile_type] = final_counts.get(tile_type, 0) + 1
        
        # 验证每种类型的方块数量
        for tile_type, count in final_counts.items():
            if count % 3 == 0:
                self.stdout.write(f"验证通过: 类型 {tile_type} 的方块数 {count} 是3的倍数")
            else:
                self.stdout.write(f"验证失败: 类型 {tile_type} 的方块数 {count} 不是3的倍数")
        
        return layout
