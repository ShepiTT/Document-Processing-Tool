#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 用于开发阶段测试主程序

作者：Lxx
更新时间：2025-09-25
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from main_gui import main
    main()
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保所有依赖文件都在同一目录下")
    input("按回车键退出...")
except Exception as e:
    print(f"程序运行出错: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...")