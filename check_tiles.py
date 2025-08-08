import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panda_match.settings')
django.setup()

# 导入模型
from game.models import Level

def check_tile_counts():
    """检查所有关卡中各类型方块的数量"""
    for level_id in range(1, 11):
        try:
            level = Level.objects.get(level_id=level_id)
            tile_counts = {}
            
            # 统计每种类型方块的数量
            for tile in level.tile_layout:
                tile_type = tile.get('type')
                if tile_type:
                    tile_counts[tile_type] = tile_counts.get(tile_type, 0) + 1
            
            # 打印统计结果
            print(f'Level {level_id}:')
            for tile_type, count in tile_counts.items():
                is_multiple_of_3 = count % 3 == 0
                print(f'  {tile_type}: {count} {"✓" if is_multiple_of_3 else "✗"}')
            
            # 检查是否所有类型都是3的倍数
            all_valid = all(count % 3 == 0 for count in tile_counts.values())
            print(f'  所有类型都是3的倍数: {"是" if all_valid else "否"}')
            print()
            
        except Level.DoesNotExist:
            print(f'Level {level_id} 不存在')

if __name__ == '__main__':
    check_tile_counts() 