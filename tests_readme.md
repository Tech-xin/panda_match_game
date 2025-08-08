# 熊猫消消乐游戏测试指南

本文档提供了如何运行熊猫消消乐游戏单元测试的说明。

## 测试文件结构

项目包含以下测试文件：

- `game/tests.py` - 游戏逻辑测试
- `game/test_models.py` - 模型测试
- `game/test_views.py` - 视图测试

## 运行测试

### 使用Django测试命令

你可以使用Django的`manage.py`命令运行测试：

```bash
python manage.py test game
```

### 使用自定义测试脚本

我们提供了一个自定义测试脚本`run_tests.py`，它提供了更多的灵活性：

```bash
# 运行所有游戏应用的测试
python run_tests.py

# 使用更详细的输出
python run_tests.py -v 2

# 运行特定的测试模块
python run_tests.py game.test_models

# 运行特定的测试类
python run_tests.py game.test_models.LevelModelTests

# 运行特定的测试方法
python run_tests.py game.test_models.LevelModelTests.test_level_creation
```

## 测试覆盖范围

我们的测试覆盖了以下方面：

### 模型测试 (`test_models.py`)

- Level模型测试
  - 创建关卡
  - 方块数量验证

- GameSession模型测试
  - 创建游戏会话
  - 缓冲区操作
  - 移除方块操作

- Tile模型测试
  - 创建方块
  - 唯一约束

- Move模型测试
  - 创建带有方块的移动
  - 创建不带方块的移动
  - 移动时间自动设置

### 游戏逻辑测试 (`tests.py`)

- 游戏板初始化
  - 使用预定义布局
  - 随机布局

- 方块操作
  - 方块可访问性检查
  - 选择方块
  - 缓冲区匹配检查

- 工具使用
  - 移除工具
  - 撤回工具
  - 洗牌工具
  - 返回移除方块

- 游戏状态检查
  - 游戏结束条件
  - 完成关卡

### 视图测试 (`test_views.py`)

- 游戏主页视图
- 开始游戏视图
- 游戏页面视图
- 选择方块视图
- 使用工具视图
- 返回移除方块视图
- 获取游戏状态视图

## 添加新测试

如果你想添加新的测试，请遵循以下步骤：

1. 确定测试应该放在哪个文件中（模型、视图或游戏逻辑）
2. 创建一个新的测试方法，方法名应以`test_`开头
3. 编写测试代码，使用Django的`TestCase`类提供的断言方法
4. 运行测试以确保它们通过

## 测试最佳实践

- 每个测试方法应该只测试一个功能
- 使用`setUp`方法创建测试所需的对象
- 使用有意义的测试方法名称
- 添加文档字符串说明测试的目的
- 使用断言方法验证结果