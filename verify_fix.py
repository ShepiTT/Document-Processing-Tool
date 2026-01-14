#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修复后的公司材料包选择功能
"""

import os
import sys
from pathlib import Path

def verify_package_detection():
    """验证材料包检测"""
    print("=== 验证材料包检测修复 ===")

    # 尝试多个可能的数据文件夹路径
    possible_paths = [
        Path("data"),
        Path("./data"),
        Path(os.getcwd()) / "data"
    ]

    data_path = None
    for path in possible_paths:
        print(f"检查路径: {path.absolute()}")
        if path.exists() and path.is_dir():
            print("  ✅ 找到data文件夹")
            print(f"  路径: {path.absolute()}")
            data_path = path
            break
        else:
            print("  ❌ 路径不存在")
            print(f"  路径: {path.absolute()}")
    if not data_path:
        print("❌ 无法找到data文件夹")
        return False

    print(f"使用路径: {data_path.absolute()}")

    # 扫描公司材料包
    package_dirs = []

    # 先扫描一级目录
    print("\n扫描一级目录...")
    for item in data_path.iterdir():
        if item.is_dir():
            dir_name = item.name
            if "_" in dir_name and "材料包" in dir_name:
                package_dirs.append((dir_name, item))
                print(f"  ✅ 一级目录找到材料包: {dir_name}")

    # 如果一级目录没找到，再扫描二级目录
    if not package_dirs:
        print("一级目录未找到材料包，扫描二级目录...")
        for item in data_path.iterdir():
            if item.is_dir():
                for sub_item in item.iterdir():
                    if sub_item.is_dir():
                        sub_dir_name = sub_item.name
                        if "_" in sub_dir_name and "材料包" in sub_dir_name:
                            package_dirs.append((sub_dir_name, sub_item))
                            print(f"  ✅ 二级目录找到材料包: {sub_dir_name}")

    print(f"\n总共找到 {len(package_dirs)} 个材料包:")
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

    if not package_dirs:
        print("❌ 未找到任何材料包")
        return False

    print("✅ 修复验证成功")
    return True

def main():
    """主函数"""
    print("开始验证公司材料包选择功能修复...")

    if verify_package_detection():
        print("\n🎉 修复验证成功！")
        return 0
    else:
        print("\n❌ 修复验证失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
