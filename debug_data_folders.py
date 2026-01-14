#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试data文件夹内容
"""

import os
import sys
from pathlib import Path

def debug_data_folders():
    """调试data文件夹内容"""
    print("=== 调试data文件夹内容 ===")

    # 检查当前工作目录
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")

    # 尝试不同的路径
    possible_paths = [
        "data",
        "./data",
        "../data",
        os.path.join(cwd, "data")
    ]

    data_path = None
    for path in possible_paths:
        full_path = Path(path).resolve()
        print(f"检查路径: {full_path}")
        if full_path.exists():
            print(f"  ✅ 找到路径: {full_path}")
            data_path = full_path
            break
        else:
            print(f"  ❌ 路径不存在: {full_path}")

    if not data_path:
        print("❌ 无法找到data文件夹")
        return False

    print(f"\ndata文件夹内容:")
    print(f"完整路径: {data_path.absolute()}")

    # 列出所有项目
    all_items = list(data_path.iterdir())
    print(f"\n发现 {len(all_items)} 个项目:")

    for item in all_items:
        print(f"  {'📁' if item.is_dir() else '📄'} {item.name}")

        if item.is_dir():
            # 检查是否是材料包格式
            dir_name = item.name
            has_underscore = "_" in dir_name
            has_package_keyword = "材料包" in dir_name

            print(f"    包含下划线: {'✅' if has_underscore else '❌'}")
            print(f"    包含'材料包': {'✅' if has_package_keyword else '❌'}")

            if has_underscore and has_package_keyword:
                print(f"    ✅ 符合材料包格式: {dir_name}")

                # 检查子文件夹
                print(f"    子文件夹:")
                subdirs = [sub for sub in item.iterdir() if sub.is_dir()]
                for subdir in sorted(subdirs):
                    print(f"      📁 {subdir.name}")

                print(f"    文件夹数量: {len(subdirs)}")
            else:
                print(f"    ❌ 不符合材料包格式")
        print()

    # 专门查找材料包
    print("=== 查找材料包 ===")
    package_dirs = []
    for item in data_path.iterdir():
        if item.is_dir():
            dir_name = item.name
            if "_" in dir_name and "材料包" in dir_name:
                package_dirs.append((dir_name, item))

    print(f"找到 {len(package_dirs)} 个材料包:")
    for package_name, package_path in package_dirs:
        print(f"  📦 {package_name}")
        print(f"     路径: {package_path}")

        # 检查关键文件夹
        critical_folders = [
            "1.监管信息-1.2申请表",
            "1.监管信息-1.4产品列表",
            "7.营业执照"
        ]

        print(f"     关键文件夹检查:")
        for folder in critical_folders:
            folder_path = package_path / folder
            if folder_path.exists():
                file_count = len(list(folder_path.rglob('*')))
                print(f"       ✅ {folder}: {file_count} 个文件")
            else:
                print(f"       ❌ {folder}: 不存在")

    return True

if __name__ == "__main__":
    debug_data_folders()
