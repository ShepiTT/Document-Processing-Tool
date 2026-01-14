#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径辅助工具模块
统一管理资源路径和应用路径的获取

作者：Lxx
"""

import os
import sys


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（用于template等打包资源）
    
    打包后返回临时解压目录；开发环境返回当前工作目录
    """
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_app_path(relative_path=""):
    """获取应用程序运行目录的路径（用于data、output等用户数据目录）
    
    打包后返回exe所在目录；开发环境返回当前工作目录
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    
    if relative_path:
        return os.path.join(base_path, relative_path)
    return base_path


def ensure_dir(path):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path
