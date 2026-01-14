#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗器械文档处理工具集 - 缓存管理器
独立于主程序的缓存管理模块，用于保存和恢复界面状态

作者：Lxx   更新时间：2025-10-13
"""

import os
import json
import sys
from pathlib import Path


class GUICacheManager:
    """界面缓存管理器，用于保存和恢复界面状态"""

    def __init__(self, cache_file="gui_cache.json"):
        """
        初始化缓存管理器

        Args:
            cache_file: 缓存文件名，默认为gui_cache.json
        """
        # 获取程序运行的实际目录（支持打包后的exe）
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境：使用exe所在目录
            application_path = os.path.dirname(sys.executable)
        else:
            # 开发环境：使用当前工作目录
            application_path = os.path.abspath(".")
        
        # 确保缓存文件夹存在（在exe同级目录下）
        self.cache_dir = os.path.join(application_path, ".cache")
        self._ensure_cache_directory()

        # 设置完整的缓存文件路径
        self.cache_file = os.path.join(self.cache_dir, cache_file)

        self.default_cache = {
            "window": {
                "width": 1280,
                "height": 720,
                "x": None,
                "y": None
            },
            "templates": {
                "selected_rename_template": None,
                "selected_extract_template": None,
                "selected_word_template": None,
                "selected_clean_template": None,
                "selected_material_package_template": None
            },
            "paths": {
                "current_package_path": None
            },
            "ui_state": {
                "last_used_templates": []
            }
        }

    def _ensure_cache_directory(self):
        """
        确保缓存目录存在，如果不存在则创建
        """
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                print(f"[缓存管理器] 已创建缓存目录: {self.cache_dir}")
            else:
                print(f"[缓存管理器] 使用缓存目录: {self.cache_dir}")
        except Exception as e:
            print(f"[缓存管理器] 创建缓存目录失败: {e}")
            print(f"[缓存管理器] 尝试的路径: {self.cache_dir}")

    def load_cache(self):
        """
        加载缓存数据

        Returns:
            dict: 缓存数据，如果加载失败则返回默认缓存
        """
        try:
            if os.path.exists(self.cache_file):
                print(f"[缓存管理器] 正在加载缓存: {self.cache_file}")
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[缓存管理器] 缓存加载成功")
                    return data
            else:
                print(f"[缓存管理器] 缓存文件不存在，使用默认配置")
                print(f"[缓存管理器] 缓存文件路径: {self.cache_file}")
                return self.default_cache.copy()
        except Exception as e:
            print(f"[缓存管理器] 加载缓存失败: {e}")
            print(f"[缓存管理器] 缓存文件路径: {self.cache_file}")
            return self.default_cache.copy()

    def save_cache(self, data):
        """
        保存缓存数据

        Args:
            data: 要保存的缓存数据
        """
        try:
            # 确保目录存在
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
                print(f"[缓存管理器] 创建缓存目录: {cache_dir}")
            
            print(f"[缓存管理器] 正在保存缓存: {self.cache_file}")
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[缓存管理器] 缓存保存成功")
        except Exception as e:
            print(f"[缓存管理器] 保存缓存失败: {e}")
            print(f"[缓存管理器] 缓存文件路径: {self.cache_file}")

    def get_window_geometry(self, root):
        """
        获取窗口几何信息

        Args:
            root: Tkinter根窗口对象

        Returns:
            dict: 窗口几何信息
        """
        try:
            return {
                "width": root.winfo_width(),
                "height": root.winfo_height(),
                "x": root.winfo_x(),
                "y": root.winfo_y()
            }
        except:
            return {"width": 1280, "height": 720, "x": None, "y": None}

    def set_window_geometry(self, root, geometry):
        """
        设置窗口几何信息

        Args:
            root: Tkinter根窗口对象
            geometry: 几何信息字典
        """
        try:
            width = geometry.get("width", 1280)
            height = geometry.get("height", 720)
            x = geometry.get("x")
            y = geometry.get("y")

            if x is not None and y is not None:
                root.geometry(f"{width}x{height}+{x}+{y}")
            else:
                root.geometry(f"{width}x{height}")
        except Exception as e:
            print(f"设置窗口几何失败: {e}")
            root.geometry("1280x720")

    def update_window_cache(self, root, cache_data):
        """
        更新窗口缓存信息

        Args:
            root: Tkinter根窗口对象
            cache_data: 缓存数据字典
        """
        cache_data["window"] = self.get_window_geometry(root)

    def update_templates_cache(self, cache_data, **templates):
        """
        更新模板缓存信息

        Args:
            cache_data: 缓存数据字典
            **templates: 模板参数，如selected_rename_template等
        """
        templates_cache = cache_data.setdefault("templates", {})
        for key, value in templates.items():
            if key.startswith("selected_") and key.endswith("_template"):
                templates_cache[key] = value

    def update_paths_cache(self, cache_data, **paths):
        """
        更新路径缓存信息

        Args:
            cache_data: 缓存数据字典
            **paths: 路径参数，如current_package_path等
        """
        paths_cache = cache_data.setdefault("paths", {})
        paths_cache.update(paths)

    def save_cache_data(self, root, templates=None, paths=None, ui_state=None):
        """
        保存完整的缓存数据

        Args:
            root: Tkinter根窗口对象
            templates: 模板信息字典
            paths: 路径信息字典
            ui_state: UI状态信息字典
        """
        try:
            # 加载现有缓存
            cache_data = self.load_cache()

            # 更新窗口几何信息
            self.update_window_cache(root, cache_data)

            # 更新模板信息
            if templates:
                self.update_templates_cache(cache_data, **templates)

            # 更新路径信息
            if paths:
                self.update_paths_cache(cache_data, **paths)

            # 更新UI状态信息
            if ui_state:
                cache_data.setdefault("ui_state", {}).update(ui_state)

            # 保存到文件
            self.save_cache(cache_data)

        except Exception as e:
            print(f"保存缓存数据失败: {e}")

    def get_cache_value(self, key_path, default=None):
        """
        获取缓存中的特定值

        Args:
            key_path: 键路径，如 "templates.selected_rename_template"
            default: 默认值

        Returns:
            缓存值或默认值
        """
        try:
            cache_data = self.load_cache()

            # 支持嵌套键路径，如 "templates.selected_rename_template"
            keys = key_path.split('.')
            value = cache_data

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value
        except Exception as e:
            print(f"获取缓存值失败 {key_path}: {e}")
            return default

    def set_cache_value(self, key_path, value):
        """
        设置缓存中的特定值

        Args:
            key_path: 键路径，如 "templates.selected_rename_template"
            value: 要设置的值
        """
        try:
            cache_data = self.load_cache()

            # 支持嵌套键路径
            keys = key_path.split('.')
            current = cache_data

            # 导航到父级字典
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # 设置最终值
            current[keys[-1]] = value

            # 保存缓存
            self.save_cache(cache_data)

        except Exception as e:
            print(f"设置缓存值失败 {key_path}: {e}")

    def clear_cache(self):
        """清空缓存文件"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                print("缓存已清空")
        except Exception as e:
            print(f"清空缓存失败: {e}")

    def export_cache(self, export_path):
        """
        导出缓存到指定文件

        Args:
            export_path: 导出文件路径
        """
        try:
            cache_data = self.load_cache()
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"缓存已导出到: {export_path}")
        except Exception as e:
            print(f"导出缓存失败: {e}")

    def import_cache(self, import_path):
        """
        从指定文件导入缓存

        Args:
            import_path: 导入文件路径
        """
        try:
            if os.path.exists(import_path):
                with open(import_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)

                # 验证导入的数据结构
                if isinstance(imported_data, dict):
                    self.save_cache(imported_data)
                    print(f"缓存已从 {import_path} 导入")
                else:
                    print("导入失败：文件格式不正确")
            else:
                print(f"导入失败：文件不存在 {import_path}")
        except Exception as e:
            print(f"导入缓存失败: {e}")


def create_cache_manager(cache_file="gui_cache.json"):
    """
    创建缓存管理器实例的便捷函数

    Args:
        cache_file: 缓存文件名

    Returns:
        GUICacheManager: 缓存管理器实例
    """
    return GUICacheManager(cache_file)


if __name__ == "__main__":
    # 独立测试缓存功能
    print("🧪 缓存管理器独立测试")

    # 创建缓存管理器
    cache_mgr = create_cache_manager("test_cache.json")

    # 测试基本功能
    test_data = {
        "test_key": "test_value",
        "test_number": 42,
        "test_dict": {"nested": "value"}
    }

    print("保存测试数据...")
    cache_mgr.save_cache(test_data)

    print("读取测试数据...")
    loaded = cache_mgr.load_cache()
    print(f"读取结果: {loaded}")

    # 测试键值操作
    print("测试键值操作...")
    cache_mgr.set_cache_value("test_key", "updated_value")
    value = cache_mgr.get_cache_value("test_key", "default")
    print(f"获取的键值: {value}")

    # 清理测试文件
    cache_mgr.clear_cache()
    print("✅ 缓存管理器测试完成")
