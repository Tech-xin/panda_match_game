import random

from collections import Counter
from .models import Tile, Move

class GameBoard:
    """
    Class to manage the game board and game logic
    """
    TILE_TYPES = ['bamboo', 'leaf', 'panda', 'fish', 'carrot', 'fire']

    def __init__(self, game_session):
        self.game_session = game_session
        self.level = game_session.level

        # 首先从数据库加载缓冲区状态，而不是创建空数组
        self.buffer = self.game_session.buffer if hasattr(self.game_session, 'buffer') and self.game_session.buffer else []

        # 加载移出的方块
        self.removed_tiles = self.game_session.removed_tiles if hasattr(self.game_session, 'removed_tiles') and self.game_session.removed_tiles else []

        # 然后加载游戏板，这样可以排除已经在缓冲区的方块
        self.board = self.load_board()

    def save_buffer_state(self):
        """保存缓冲区和移出方块状态到数据库"""
        self.game_session.buffer = self.buffer
        self.game_session.removed_tiles = self.removed_tiles
        self.game_session.save(update_fields=['buffer', 'removed_tiles'])


    def load_board(self):
        """
        Load the current game board from the database
        """
        # 只加载不在缓冲区和移出方块中的方块
        buffer_tile_ids = [tile['id'] for tile in self.buffer] if self.buffer else []
        removed_tile_ids = [tile['id'] for tile in self.removed_tiles] if self.removed_tiles else []
        excluded_tile_ids = buffer_tile_ids + removed_tile_ids

        tiles = Tile.objects.filter(game_session=self.game_session).exclude(tile_id__in=excluded_tile_ids)
        board = {}

        for tile in tiles:
            key = f"{tile.position_x},{tile.position_y},{tile.layer}"
            board[key] = {
                'id': tile.tile_id,
                'type': tile.tile_type,
                'x': tile.position_x,
                'y': tile.position_y,
                'z': tile.position_z,
                'layer': tile.layer
            }

        return board

    def initialize_board(self, rows=5, cols=5, layers=None):
        """
        Initialize the game board based on level configuration
        """
        print(f"初始化游戏板，关卡={self.level.level_id}，难度={self.level.difficulty}")

        # 清空所有现有方块
        Tile.objects.filter(game_session=self.game_session).delete()

        # 获取方块配置
        level_tiles = self.level.tile_layout

        # 如果关卡配置为空，使用默认配置
        if not level_tiles:
            # 基于难度生成随机方块类型
            difficulty = self.level.difficulty
            num_tiles = 36 + (difficulty - 1) * 12  # 难度 1: 36 方块, 难度 2: 48 方块, etc.

            # 确保方块数量是 3 的倍数
            if num_tiles % 3 != 0:
                num_tiles += 3 - (num_tiles % 3)

            # 随机生成方块
            tile_types = []
            for i in range(num_tiles // 3):
                tile_type = random.choice(list(dict(Tile.TILE_TYPES).keys()))
                # 每个类型重复3次（以便有机会匹配）
                tile_types.extend([tile_type] * 3)

            # 如果有随机洗牌，打乱方块顺序
            random.shuffle(tile_types)

            # 处理层级
            if not layers:
                # 根据难度设置层数
                # 难度1：1层，难度2：1-2层，难度3：1-3层，难度4：1-4层，难度5：1-5层
                max_layer = min(5, difficulty)

                # 创建堆叠方块的规则：
                # 1. 确定有多少个位置会有堆叠方块
                # 2. 对于这些位置，随机生成1-3个堆叠高度
                # 3. 生成连续的层级，确保不会有"空洞"
                stacked_positions = int(num_tiles * 0.3)  # 30%的位置会有堆叠方块
                max_stack_height = max_layer

                # 创建基础位置（所有方块的底层）
                positions = []
                base_positions = []
                for i in range(num_tiles - stacked_positions):
                    x = random.randint(0, rows - 1)
                    y = random.randint(0, cols - 1)
                    base_positions.append((x, y))
                    positions.append((x, y, 0))  # 底层方块，层级为0

                # 为一些位置添加堆叠方块（随机选择一些已有的位置）
                if stacked_positions > 0 and base_positions:
                    for _ in range(stacked_positions):
                        # 随机选择一个已存在的底层位置
                        idx = random.randint(0, len(base_positions) - 1)
                        x, y = base_positions[idx]

                        # 确定堆叠高度（1-3个额外方块，加上底层方块）
                        stack_height = min(max_stack_height, random.randint(1, 3))

                        # 添加连续的堆叠方块（层级从1开始，底层已经是0）
                        for layer in range(1, stack_height + 1):
                            positions.append((x, y, layer))

                random.shuffle(positions)
            else:
                # 使用提供的层级列表
                positions = []
                for i in range(num_tiles):
                    x = random.randint(0, rows - 1)
                    y = random.randint(0, cols - 1)
                    layer = layers[i]
                    positions.append((x, y, layer))
        else:
            # 使用配置的方块布局
            tile_types = []
            positions = []

            for tile_info in level_tiles:
                tile_types.append(tile_info['type'])
                x = tile_info['x']
                y = tile_info['y']
                # 如果指定了层，则使用配置的层
                layer = tile_info.get('layer', 0)
                positions.append((x, y, layer))

        # 创建游戏板
        board = {}

        # 生成可用位置
        available_positions = []
        for x, y, layer in positions:
            # 为每个方块添加一个 z 坐标（用于 3D 效果）
            # 使用 layer 值作为 z_pos 的基础，并加上一个唯一的增量，确保唯一性
            z_pos = layer  # 修改：使用 layer 值作为 z_pos 以确保唯一性
            available_positions.append((x, y, layer, z_pos))

        # 确保先创建底层的方块再创建高层的方块，对于相同坐标的方块按层级排序
        all_tiles = tile_types.copy()
        available_positions.sort(key=lambda pos: (pos[0], pos[1], pos[2]))  # 按x,y,layer排序

        # 创建并跟踪每个位置的堆叠方块数量
        stacked_counts = {}  # 键是 "x,y" 格式，值是该位置下方块总数

        # 放置方块到游戏板上，按位置和层级排序
        for i, (x, y, layer, z_pos) in enumerate(available_positions):
            if i >= len(all_tiles):
                break

            tile_type = all_tiles[i]

            # 跟踪堆叠方块数量
            pos_key = f"{x},{y}"
            if pos_key not in stacked_counts:
                stacked_counts[pos_key] = 1
            else:
                stacked_counts[pos_key] += 1

            # 在数据库中创建方块
            # 确保 position_z 值是唯一的 - 对每个位置使用一个唯一的组合
            # 使用 layer 作为 position_z 可能导致唯一约束错误，如果在同一个x,y位置有相同层级的方块
            try:
                tile = Tile.objects.create(
                    game_session=self.game_session,
                    tile_type=tile_type,
                    position_x=x,
                    position_y=y,
                    position_z=i,  # 使用循环索引 i 作为 position_z 以确保唯一性
                    layer=layer
                )
            except Exception as e:
                print(f"创建方块失败: {e}")
                # 如果创建失败，尝试修改position_z并重试
                tile = Tile.objects.create(
                    game_session=self.game_session,
                    tile_type=tile_type,
                    position_x=x,
                    position_y=y,
                    position_z=random.randint(1000, 9999),  # 使用一个大随机数确保唯一
                    layer=layer
                )

            # 添加到本地游戏板
            key = f"{x},{y},{layer}"
            board[key] = {
                'id': tile.tile_id,
                'type': tile_type,
                'x': x,
                'y': y,
                'z': tile.position_z,  # 使用实际创建的 position_z
                'layer': layer
            }

            # 打印堆叠信息
            if layer > 0:
                # 检查是否有底层方块
                has_lower_layer = False
                for l in range(layer):
                    lower_key = f"{x},{y},{l}"
                    if lower_key in board:
                        has_lower_layer = True
                        break

                if has_lower_layer:
                    print(f"创建堆叠方块: 位置=({x},{y},{layer}), 类型={tile_type}, 有底层方块")
                else:
                    print(f"警告: 创建堆叠方块: 位置=({x},{y},{layer}), 类型={tile_type}, 没有底层方块")

        # 初始化完成后，计算并添加每个方块的下层方块数量
        for key, tile_data in board.items():
            x, y, layer = map(int, key.split(','))
            lower_tiles_count = self.get_lower_tiles_count(x, y, layer)
            tile_data['lower_tiles_count'] = lower_tiles_count

            # 打印方块堆叠信息
            if lower_tiles_count > 0:
                print(f"方块({x},{y},{layer})下方有{lower_tiles_count}个方块")

        self.board = board
        self.buffer = []
        self.removed_tiles = []
        return board

    def is_tile_accessible(self, x, y, layer):
        """
        Check if a tile is accessible (only tiles up to layer 3 are accessible and not covered)
        """
        # 只有前三层的方块可以被访问 (layer 0, 1, 2)
        if layer > 2:
            print(f"方块({x},{y},{layer})不可访问: 层级 > 2")
            return False

        # 检查是否有更高层级的瓦片覆盖这个位置
        # 检查所有更高层的方块
        for l in range(layer + 1, 10):  # 假设最多10层
            # 检查更高层级中是否有覆盖这个位置的瓦片
            # 一个瓦片被覆盖，如果有一个更高层级的瓦片在相同的位置
            # 或者在可能重叠这个瓦片的任意四个角落位置
            for dx, dy in [(0, 0), (-1, 0), (0, -1), (-1, -1)]:
                check_key = f"{x+dx},{y+dy},{l}"
                if check_key in self.board:
                    covering_tile = self.board[check_key]
                    print(f"方块({x},{y},{layer})被方块({covering_tile['x']},{covering_tile['y']},{covering_tile['layer']})覆盖")
                    return False

        # 如果是新变得可访问的方块，打印信息
        key = f"{x},{y},{layer}"
        if key in self.board:
            print(f"方块({x},{y},{layer})可访问")

        return True

    def get_tile(self, x, y, layer):
        """
        Get tile at position (x, y, layer)
        """
        key = f"{x},{y},{layer}"
        return self.board.get(key)

    def get_lower_tiles_count(self, x, y, layer):
        """
        获取指定位置和层级下方的方块数量
        """
        count = 0
        # 检查所有可能的下层，确保连续性
        for l in range(layer):
            key = f"{x},{y},{l}"
            if key in self.board:
                count += 1
            else:
                # 如果发现缺少层，说明不连续，应该记录警告
                print(f"警告：位置({x},{y})在层级{l}没有方块，但层级{layer}有方块")
        return count

    def select_tile(self, tile_id):
        """选择一个方块并将其移动到缓冲区"""
        # 查找方块
        try:
            tile = Tile.objects.get(tile_id=tile_id, game_session=self.game_session)
            print(f"选中方块: ID={tile.tile_id}, 位置=({tile.position_x},{tile.position_y},{tile.layer}), 类型={tile.tile_type}")

            # 获取下层方块数量，确认这是用户看到的数字
            lower_tiles_count = self.get_lower_tiles_count(tile.position_x, tile.position_y, tile.layer)
            print(f"方块({tile.position_x},{tile.position_y},{tile.layer})下方有{lower_tiles_count}个方块")

            # 在移除前预先查找下层方块，以便后续处理
            lower_tiles = []
            for l in range(tile.layer-1, -1, -1):
                lower_key = f"{tile.position_x},{tile.position_y},{l}"
                if lower_key in self.board:
                    lower_tiles.append(self.board[lower_key])
                    print(f"预先找到下层方块: 位置=({tile.position_x},{tile.position_y},{l}), 类型={self.board[lower_key]['type']}")

            print(f"预先找到{len(lower_tiles)}个下层方块")

        except Tile.DoesNotExist:
            print(f"找不到方块: ID={tile_id}")
            return False

        # 检查方块是否可访问
        if not self.is_tile_accessible(tile.position_x, tile.position_y, tile.layer):
            print(f"方块不可访问: ID={tile.tile_id}, 位置=({tile.position_x},{tile.position_y},{tile.layer})")
            return False

        # 检查缓冲区是否已满(7个格子)
        if len(self.buffer) >= 7:
            print("缓冲区已满，无法添加更多方块")
            return False

        # 创建方块数据
        tile_data = {
            'id': tile.tile_id,
            'type': tile.tile_type,
            'x': tile.position_x,
            'y': tile.position_y,
            'layer': tile.layer
        }

        # 查找相同类型的方块在缓冲区中的位置
        same_type_indices = []
        for i, buffer_tile in enumerate(self.buffer):
            if buffer_tile['type'] == tile.tile_type:
                same_type_indices.append(i)

        # 如果找到相同类型的方块，将新方块插入到最后一个相同类型方块的后面
        if same_type_indices:
            last_same_type_index = same_type_indices[-1]
            self.buffer.insert(last_same_type_index + 1, tile_data)
            print(f"方块已插入到缓冲区位置 {last_same_type_index + 1}: ID={tile.tile_id}, 类型={tile.tile_type}")
        else:
            # 如果没有相同类型的方块，则添加到缓冲区末尾
            self.buffer.append(tile_data)
            print(f"方块已添加到缓冲区末尾: ID={tile.tile_id}, 类型={tile.tile_type}")

        # 从方块区移除
        key = f"{tile.position_x},{tile.position_y},{tile.layer}"
        if key in self.board:
            del self.board[key]
            print(f"方块已从游戏板移除: 位置=({tile.position_x},{tile.position_y},{tile.layer})")

        # 记录移动
        Move.objects.create(
            game_session=self.game_session,
            tile=tile,
            action='select'
        )

        # 检查是否有匹配
        self.check_buffer_matches()

        # 保存缓冲区状态到数据库
        self.save_buffer_state()

        # 更新下层方块的可访问性
        # 之前方块位置的下一层方块现在应该变得可访问
        print(f"检查位置({tile.position_x},{tile.position_y})的下层方块是否变得可访问")

        # 获取被选中方块下层的所有方块
        found_lower_tiles = []
        for l in range(tile.layer - 1, -1, -1):
            lower_key = f"{tile.position_x},{tile.position_y},{l}"
            if lower_key in self.board:
                found_lower_tiles.append((l, self.board[lower_key]))
                print(f"发现下层方块: 位置=({tile.position_x},{tile.position_y},{l}), 类型={self.board[lower_key]['type']}")
                # 立即标记为可访问（不需要等待is_tile_accessible检查）
                self.board[lower_key]['newly_exposed'] = True

        # 打印找到的下层方块数量
        print(f"共找到{len(found_lower_tiles)}个下层方块")

        # 确保最上层的下层方块现在变为可访问
        if found_lower_tiles:
            # 获取最上层的下层方块（层级最高的）
            top_lower_layer = max([layer for layer, _ in found_lower_tiles])
            top_lower_key = f"{tile.position_x},{tile.position_y},{top_lower_layer}"

            # 确保没有其他方块覆盖它
            is_accessible = True
            for l in range(top_lower_layer + 1, 10):  # 假设最多10层
                check_key = f"{tile.position_x},{tile.position_y},{l}"
                if check_key in self.board:
                    is_accessible = False
                    print(f"警告：最上层的下层方块{top_lower_key}被{check_key}覆盖，可能不可访问")
                    break

            if is_accessible:
                print(f"最上层的下层方块现在可访问: {top_lower_key}")
                # 这里可以添加额外的处理逻辑

        # 检查是否有新的可访问方块
        print("检查是否有新的可访问方块:")
        # 记录移除前不可访问的方块
        inaccessible_before = set()
        for board_key, board_tile in self.board.items():
            x, y, layer = map(int, board_key.split(','))
            if not self.is_tile_accessible(x, y, layer):
                inaccessible_before.add(board_key)

        # 移除方块后，重新检查所有方块的可访问性
        for board_key, board_tile in self.board.items():
            x, y, layer = map(int, board_key.split(','))
            # 如果方块之前不可访问但现在可访问，标记为新可访问
            if board_key in inaccessible_before and self.is_tile_accessible(x, y, layer):
                print(f"方块现在可访问: ID={board_tile['id']}, 位置=({x},{y},{layer}), 类型={board_tile['type']}")

        return True

    def check_buffer_matches(self):
        """
        Check for matches in the buffer (3 adjacent same-type tiles)
        """

        print("Checking buffer matches. Current buffer:", self.buffer)

        while True:
            # 统计每种类型的出现次数
            type_counts = Counter(tile['type'] for tile in self.buffer)

            # 找到出现 3 次及以上的类型
            matched_types = [t for t, count in type_counts.items() if count >= 3]

            if not matched_types:
                break  # 没有可以消除的块，退出循环

            # 记录被匹配的 tiles
            matched_tiles = []

            # 遍历匹配的类型，找到 **前 3 个** 该类型的块
            for t in matched_types:
                count = 0
                for tile in self.buffer:
                    if tile['type'] == t:
                        matched_tiles.append(tile)
                        count += 1
                    if count == 3:
                        break  # 只找 3 个，不要删太多

            # 从 buffer 中移除匹配的 tiles
            self.buffer = [tile for tile in self.buffer if tile not in matched_tiles]

            # 记录 match move
            Move.objects.create(
                game_session=self.game_session,
                action='match'
            )

            # 更新分数
            self.game_session.score += 10
            self.game_session.save()

            # 删除数据库里的匹配 tiles
            for matched in matched_tiles:
                Tile.objects.filter(tile_id=matched['id']).delete()

            print("Matched tiles removed:", matched_tiles)

    def use_remove_tool(self):
        """
        Use the remove tool to take out the first three tiles from buffer
        """
        if len(self.buffer) < 3:
            return False
        elif len(self.removed_tiles) >= 5:
            return False

        # Remove first three tiles from buffer
        removed = self.buffer[:3]
        self.buffer = self.buffer[3:]

        # 将移除的方块添加到removed_tiles列表
        self.removed_tiles.extend(removed)

        # 保存缓冲区状态到数据库
        self.save_buffer_state()

        # Record action
        Move.objects.create(
            game_session=self.game_session,
            action='use_remove_tool'
        )

        return True

    def return_removed_tile(self, tile_id):
        """
        将移出的方块返回到栅栏
        """
        # 检查栅栏是否已满(7个格子)
        if len(self.buffer) >= 7:
            return False

        # 查找要返回的方块
        target_tile = None
        target_index = -1

        for i, tile in enumerate(self.removed_tiles):
            if tile['id'] == tile_id:
                target_tile = tile
                target_index = i
                break

        if target_tile is None:
            return False

        # 从移出区移除
        removed_tile = self.removed_tiles.pop(target_index)

        # 查找相同类型的方块在缓冲区中的位置
        same_type_indices = []
        for i, buffer_tile in enumerate(self.buffer):
            if buffer_tile['type'] == removed_tile['type']:
                same_type_indices.append(i)

        # 如果找到相同类型的方块，将返回的方块插入到最后一个相同类型方块的后面
        if same_type_indices:
            last_same_type_index = same_type_indices[-1]
            self.buffer.insert(last_same_type_index + 1, removed_tile)
            print(f"移出的方块已插入到缓冲区位置 {last_same_type_index + 1}: ID={removed_tile['id']}, 类型={removed_tile['type']}")
        else:
            # 如果没有相同类型的方块，则添加到缓冲区末尾
            self.buffer.append(removed_tile)
            print(f"移出的方块已添加到缓冲区末尾: ID={removed_tile['id']}, 类型={removed_tile['type']}")

        # 保存缓冲区状态到数据库
        self.save_buffer_state()

        # 记录移动
        try:
            db_tile = Tile.objects.get(tile_id=tile_id)
            Move.objects.create(
                game_session=self.game_session,
                tile=db_tile,
                action='return_removed_tile'
            )
        except Tile.DoesNotExist:
            pass

        # 检查是否有匹配
        self.check_buffer_matches()
        self.save_buffer_state()

        return True

    def use_withdraw_tool(self):
        """
        Use the withdraw tool to return the most recent tile to its original position
        """
        if not self.buffer:
            return False

        # Get the last tile from buffer
        last_tile = self.buffer.pop()

        # Find the tile in database
        try:
            tile = Tile.objects.get(tile_id=last_tile['id'])

            # Return to board
            key = f"{last_tile['x']},{last_tile['y']},{last_tile['layer']}"
            self.board[key] = {
                'id': tile.tile_id,
                'type': tile.tile_type,
                'x': last_tile['x'],
                'y': last_tile['y'],
                'z': tile.position_z,
                'layer': last_tile['layer']
            }

            # Record action
            Move.objects.create(
                game_session=self.game_session,
                tile=tile,
                action='use_withdraw_tool'
            )

            # 保存缓冲区状态到数据库
            self.save_buffer_state()

            # 检查是否有新的可访问方块状态变化
            # 记录放回前可访问的方块
            accessible_before = set()
            for board_key, board_tile in self.board.items():
                x, y, layer = map(int, board_key.split(','))
                if self.is_tile_accessible(x, y, layer):
                    accessible_before.add(board_key)

            # 重新检查所有方块的可访问性
            for board_key, board_tile in self.board.items():
                x, y, layer = map(int, board_key.split(','))
                is_accessible_now = self.is_tile_accessible(x, y, layer)

                # 如果方块之前可访问但现在不可访问，或者之前不可访问但现在可访问
                if (board_key in accessible_before and not is_accessible_now) or \
                        (board_key not in accessible_before and is_accessible_now):
                    print(f"方块可访问性变化: ID={board_tile['id']}, 位置=({x},{y},{layer}), 类型={board_tile['type']}, 可访问={is_accessible_now}")

            self.save_buffer_state()
            return True
        except Tile.DoesNotExist:
            return False

    def use_shuffle_tool(self):
        """
        Use the shuffle tool to randomize all remaining tiles on the board
        """
        # Get all tiles in the board
        tiles = list(self.board.values())

        if not tiles:
            return False

        # Shuffle the tile types
        tile_types = [tile['type'] for tile in tiles]
        random.shuffle(tile_types)

        # Update tiles with new types
        for i, tile in enumerate(tiles):
            db_tile = Tile.objects.get(tile_id=tile['id'])
            db_tile.tile_type = tile_types[i]
            db_tile.save()

            # Update local board
            key = f"{tile['x']},{tile['y']},{tile['layer']}"
            self.board[key]['type'] = tile_types[i]

        # Record action
        Move.objects.create(
            game_session=self.game_session,
            action='use_shuffle_tool'
        )

        self.save_buffer_state()
        return True

    def is_game_over(self):
        """
        Check if the game is over (board is empty or no more possible matches)
        """
        # 如果还有移出的方块，游戏未结束
        if self.removed_tiles:
            return False

        # 如果还有方块在游戏板上，游戏未结束
        if self.board:
            return False

        # 如果缓冲区为空，游戏结束
        if not self.buffer:
            return True

        # 检查缓冲区中是否有可能的匹配
        # 如果缓冲区中有3个或更多相同类型的方块，游戏未结束
        type_counts = {}
        for tile in self.buffer:
            type_counts[tile['type']] = type_counts.get(tile['type'], 0) + 1

        print(f"缓冲区中的方块类型分布: {type_counts}")

        # 检查是否有任何类型的方块数量不是3的倍数
        for tile_type, count in type_counts.items():
            if count % 3 != 0:
                print(f"警告: 缓冲区中类型 {tile_type} 的方块数 {count} 不是3的倍数")
                # 如果有任何类型的方块数量不是3的倍数，游戏可能无法完成
                # 但我们不在这里结束游戏，因为玩家可能还有道具可以使用

        # 如果有任何类型的方块数量大于等于3，游戏未结束
        if any(count >= 3 for count in type_counts.values()):
            return False

        # 如果缓冲区已满且没有可能的匹配，游戏卡住了
        if len(self.buffer) == 7:
            return True

        # 其他情况，游戏未结束
        return False

    def complete_level(self):
        """
        Mark level as completed
        """
        self.game_session.status = 'completed'
        self.game_session.save()

        # Update player's level progress if needed
        player = self.game_session.player
        if player.level_progress <= self.level.level_id:
            player.level_progress = self.level.level_id + 1
            player.save()

        return True