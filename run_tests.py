#!/usr/bin/env python
import os
import sys
import django
import argparse

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game.test_settings')
django.setup()

# 导入测试运行器
from django.test.runner import DiscoverRunner

def run_tests(test_labels=None, verbosity=1):
    """运行指定的测试或所有测试"""
    # 如果没有指定测试标签，则运行游戏应用的所有测试
    if not test_labels:
        test_labels = ['game']
    
    # 创建测试运行器
    test_runner = DiscoverRunner(verbosity=verbosity)
    
    # 运行测试
    failures = test_runner.run_tests(test_labels)
    
    # 返回退出代码
    return bool(failures)

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='运行单元测试')
    parser.add_argument('test_labels', nargs='*', help='要运行的测试标签，例如 game.tests.LevelModelTests')
    parser.add_argument('-v', '--verbosity', type=int, choices=[0, 1, 2, 3], default=1, help='测试输出的详细程度')
    args = parser.parse_args()
    
    # 运行测试
    sys.exit(run_tests(args.test_labels, args.verbosity)) 