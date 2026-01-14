#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗器械文档处理工具 - 优化打包脚本
减小exe体积的版本

用法：
  python build_exe_optimized.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_dirs():
    """清理之前的构建目录"""
    print("正在清理旧的构建文件...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  [OK] 已删除 {dir_name}")
            except Exception as e:
                print(f"  [错误] 删除 {dir_name} 失败: {e}")


def build_exe():
    """构建exe文件（优化体积）"""
    print("\n开始打包程序（优化模式）...")

    cmd = [
        'pyinstaller',
        '--name=医疗器械文档处理工具',
        '--onedir',
        '--windowed',
        '--noconfirm',
        '--clean',

        # 添加数据文件
        '--add-data=template;template',
        '--add-data=version.json;.',

        # 只添加必要的隐藏导入（精简版）
        '--hidden-import=win32com.client',
        '--hidden-import=pythoncom',
        '--hidden-import=pywintypes',
        '--hidden-import=path_helper',

        # ========== 关键：排除不需要的大型模块 ==========
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=sklearn',
        '--exclude-module=tensorflow',
        '--exclude-module=torch',
        '--exclude-module=cv2',
        '--exclude-module=opencv',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        '--exclude-module=pytest',
        '--exclude-module=unittest',
        '--exclude-module=setuptools',
        '--exclude-module=pip',
        '--exclude-module=wheel',
        '--exclude-module=openai',
        '--exclude-module=pytesseract',  # 如果不用OCR可以排除
        '--exclude-module=email',
        '--exclude-module=html',
        '--exclude-module=http',
        '--exclude-module=xml',
        '--exclude-module=logging.handlers',
        '--exclude-module=multiprocessing',
        '--exclude-module=concurrent',
        '--exclude-module=asyncio',
        '--exclude-module=lib2to3',
        '--exclude-module=distutils',
        '--exclude-module=pkg_resources',

        # 主程序文件
        'main_gui.py'
    ]

    print(f"\n执行命令:\n{' '.join(cmd)}\n")
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print("\n[成功] 打包成功！")
            return True
    except subprocess.CalledProcessError as e:
        print(f"\n[失败] 打包失败: {e}")
        return False
    except Exception as e:
        print(f"\n[错误] 打包过程出错: {e}")
        return False


def create_folders():
    """在dist目录中创建必要的文件夹"""
    print("\n创建必要的文件夹...")
    dist_dir = Path('dist/医疗器械文档处理工具')

    for folder in ['data', 'output', 'log']:
        folder_path = dist_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] 已创建 {folder}")


def main():
    print("=" * 60)
    print("医疗器械文档处理工具 - 优化打包脚本")
    print("=" * 60)

    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("[提示] 正在安装PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    clean_build_dirs()

    if not build_exe():
        print("\n打包失败！")
        return 1

    create_folders()

    print("\n" + "=" * 60)
    print("[完成] 打包完成！")
    print("=" * 60)
    print(f"\n可执行文件: dist\\医疗器械文档处理工具\\医疗器械文档处理工具.exe")

    return 0


if __name__ == '__main__':
    sys.exit(main())
