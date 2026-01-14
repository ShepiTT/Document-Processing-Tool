#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹清理工具
清理指定文件夹，只保留材料包文件夹，删除其他内容
用于医疗器械文档处理流程的文件夹整理

作者：Lxx  
更新时间：2025-10-15
"""

import os
import sys
import shutil
import json

from path_helper import get_resource_path, get_app_path


def load_clean_config():
    """加载清理配置模板"""
    config_path = get_resource_path(os.path.join("template", "clean_templates", "clean_config.json"))

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  清理配置模板不存在: {config_path}，使用默认配置")
        return get_default_clean_config()
    except json.JSONDecodeError:
        print(f"⚠️  清理配置模板格式错误: {config_path}，使用默认配置")
        return get_default_clean_config()

def get_default_clean_config():
    """获取默认清理配置"""
    return {
        "rules": [
            {
                "pattern": "*_材料包",
                "type": "folder"
            }
        ]
    }

def find_items_to_keep(target_folder, config):
    """找到要保留的项目（文件夹或文件）"""
    items_to_keep = []

    # 获取启用的规则
    enabled_rules = config.get("rules", [])

    # 遍历目标文件夹中的项目
    try:
        for item in os.listdir(target_folder):
            item_path = os.path.join(target_folder, item)
            is_dir = os.path.isdir(item_path)
            is_file = os.path.isfile(item_path)

            # 检查每个规则
            for rule in enabled_rules:
                pattern = rule.get("pattern", "")
                item_type = rule.get("type", "folder")
                extension = rule.get("extension", "")

                # 检查是否匹配类型
                if item_type == "folder" and not is_dir:
                    continue
                if item_type == "file" and not is_file:
                    continue

                # 检查是否匹配模式
                if matches_pattern(item, pattern):
                    # 如果是文件类型，检查扩展名
                    if item_type == "file" and extension:
                        if not item.lower().endswith(extension.lower()):
                            continue

                    items_to_keep.append(item)
                    item_desc = "文件夹" if is_dir else f"文件({extension})"
                    print(f"  ✅ 保留{item_desc}: {item}")
                    break

    except PermissionError:
        print(f"  ❌ 无权限访问文件夹: {target_folder}")
        return []

    return items_to_keep

def matches_pattern(item_name, pattern):
    """检查项目名称是否匹配模式"""
    import fnmatch
    return fnmatch.fnmatch(item_name, pattern)

def clean_folder(target_folder, config_path=None, gui_mode=False, confirmation_callback=None):
    """
    清理指定文件夹，只保留材料包文件夹，删除其他内容

    Args:
        target_folder: 要清理的目标文件夹
        config_path: 配置文件路径，如果为None则使用默认配置
        gui_mode: 是否为GUI模式
        confirmation_callback: GUI模式下的确认回调函数
    """

    # 加载配置
    if config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置失败: {e}，使用默认配置")
            config = get_default_clean_config()
    else:
        config = load_clean_config()

    # 找到要保留的项目
    items_to_keep = find_items_to_keep(target_folder, config)

    if not items_to_keep:
        print(f"  ❌ 在 {target_folder} 中未找到符合保留规则的项目")
        return False, 0

    print(f"  📋 找到 {len(items_to_keep)} 个要保留的项目:")
    for item in items_to_keep:
        print(f"    - {item}")

    # 获取要删除的项目列表
    items_to_delete = []
    for item in os.listdir(target_folder):
        # 跳过要保留的项目
        if item in items_to_keep:
            continue

        items_to_delete.append(item)

    if not items_to_delete:
        print(f"  ℹ️  没有需要删除的内容")
        return True, 0

    print(f"  📋 将要删除的项目 ({len(items_to_delete)} 个):")
    for item in items_to_delete:
        print(f"    - {item}")

    # 检查是否需要确认删除
    if config.get("processing_options", {}).get("confirm_deletion", True):
        if not gui_mode:
            confirm = input("确认执行删除操作吗？(输入 'yes' 确认): ")
            if confirm.lower() != 'yes':
                print("❌ 操作已取消")
                return False, 0
        else:
            # GUI模式下使用回调函数
            if confirmation_callback:
                message = f"即将删除以下项目：\n\n"
                for item in items_to_delete[:10]:  # 最多显示10个
                    message += f"• {item}\n"
                if len(items_to_delete) > 10:
                    message += f"\n... 还有 {len(items_to_delete) - 10} 个项目\n"
                message += f"\n总共将删除 {len(items_to_delete)} 个项目，是否继续？"

                if not confirmation_callback("确认删除", message):
                    print("❌ 用户取消了操作")
                    return False, 0

    # 执行删除操作
    deleted_count = 0
    for item in items_to_delete:
        item_path = os.path.join(target_folder, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"    🗂️  已删除文件夹: {item}")
            else:
                os.remove(item_path)
                print(f"    📄 已删除文件: {item}")
            deleted_count += 1
        except Exception as e:
            print(f"    ❌ 删除 {item} 时出错: {e}")

    print(f"  ✅ 清理完成！删除了 {deleted_count} 个项目，保留: {items_to_keep}")
    return True, deleted_count

def process_data_folders(gui_mode=False, confirmation_callback=None):
    """
    遍历data文件夹中的所有子文件夹并执行清理操作
    参数:
        gui_mode: 是否为GUI模式
        confirmation_callback: GUI模式下的确认回调函数
    """
    data_folder = get_app_path("data")
    
    # 检查data文件夹是否存在
    if not os.path.exists(data_folder):
        print(f"❌ 文件夹不存在: {data_folder}")
        return
    
    if not os.path.isdir(data_folder):
        print(f"❌ 路径不是文件夹: {data_folder}")
        return
    
    # 获取data文件夹中的所有子文件夹
    subfolders = []
    for item in os.listdir(data_folder):
        item_path = os.path.join(data_folder, item)
        if os.path.isdir(item_path):
            subfolders.append(item)
    
    if not subfolders:
        print("❌ data文件夹中没有找到任何子文件夹")
        return
    
    print(f"🔍 在data文件夹中找到 {len(subfolders)} 个子文件夹:")
    for folder in subfolders:
        print(f"  - {folder}")
    
    # 确认批量操作
    if not gui_mode:
        print(f"\n⚠️  即将对以上所有文件夹执行清理操作（只保留材料包文件夹）")
        confirm = input("确认继续批量处理吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            return
    else:
        # GUI模式下的确认
        if confirmation_callback:
            message = f"即将对以下 {len(subfolders)} 个文件夹进行清理处理：\n\n"
            for folder in subfolders[:10]:  # 最多显示10个
                message += f"• {folder}\n"
            if len(subfolders) > 10:
                message += f"\n... 还有 {len(subfolders) - 10} 个文件夹\n"
            message += "\n清理操作将删除非材料包文件夹，只保留以「_材料包」结尾的文件夹。\n\n此操作不可逆，是否继续？"
            
            if not confirmation_callback("确认批量清理", message):
                print("❌ 用户取消了操作")
                return
    
    # 统计信息
    total_processed = 0
    successful_count = 0
    total_deleted_items = 0
    
    print(f"\n🚀 开始批量处理...")
    print("=" * 60)
    
    # 遍历并处理每个子文件夹
    for folder in subfolders:
        folder_path = os.path.join(data_folder, folder)
        print(f"\n📁 正在处理: {folder}")
        
        success, deleted_count = clean_folder(folder_path, gui_mode=gui_mode, confirmation_callback=confirmation_callback)
        total_processed += 1
        if success:
            successful_count += 1
            total_deleted_items += deleted_count
    
    # 显示最终统计结果
    print("\n" + "=" * 60)
    print("📊 批量处理完成！统计结果:")
    print(f"  📁 总处理文件夹数: {total_processed}")
    print(f"  ✅ 成功处理数: {successful_count}")
    print(f"  ❌ 失败处理数: {total_processed - successful_count}")
    print(f"  🗑️  总删除项目数: {total_deleted_items}")

def main():
    print("🧹 批量文件夹清理工具")
    print("=" * 60)
    print("功能：遍历data文件夹中的所有子文件夹，只保留材料包文件夹，删除其他内容")
    print("=" * 60)
    
    process_data_folders()

if __name__ == "__main__":
    main()
