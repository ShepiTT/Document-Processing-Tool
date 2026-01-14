#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用文件重命名工具
基于JSON模板进行批量文件重命名
支持多种文件类型和自定义命名规则

作者：Lxx
更新时间：2025-10-15
"""

import os
import re
import json
import sys
from pathlib import Path

from path_helper import get_resource_path, get_app_path


class UniversalFileRenamer:
    def __init__(self, template_name="牙科手机模板"):
        # 从templates目录加载模板文件
        self.templates = self._load_templates()
        
        # 设置当前使用的模板
        self.current_template = template_name
        if template_name not in self.templates:
            print(f"⚠️  模板 '{template_name}' 不存在，使用默认牙科手机模板")
            self.current_template = "牙科手机模板"

        # 获取模板配置
        template_data = self.templates[self.current_template]
        self.file_rules = template_data["rules"]
        
        # 默认支持的后缀，增加xlsx和png，且统一转为小写以支持大小写不区分
        default_extensions = [".pdf", ".doc", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"]
        raw_extensions = template_data.get("supported_extensions", default_extensions)
        self.supported_extensions = [ext.lower() for ext in raw_extensions]
    
    def _load_templates(self):
        """从template/rename_templates目录加载所有JSON模板文件"""
        templates = {}
        templates_dir = Path(get_resource_path("template/rename_templates"))

        if not templates_dir.exists():
            print(f"❌ template/rename_templates目录不存在: {templates_dir}")
            print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
            print(f"[DEBUG] 资源基础路径: {get_resource_path('.')}")
            return templates
        
        # 遍历template/rename_templates目录中的所有JSON文件
        for json_file in templates_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                # 使用文件名（不含扩展名）作为模板键名
                template_key = json_file.stem
                templates[template_key] = template_data
                
            except Exception as e:
                print(f"⚠️  加载模板文件 {json_file} 失败: {e}")
                continue
        
        if not templates:
            print("❌ 没有找到有效的模板文件")
        
        return templates
    
    def get_available_templates(self):
        """获取所有可用的模板列表"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name):
        """获取指定模板的详细信息"""
        if template_name in self.templates:
            return self.templates[template_name]
        return None
    
    def switch_template(self, template_name):
        """切换到指定的模板"""
        if template_name in self.templates:
            self.current_template = template_name
            template_data = self.templates[template_name]
            self.file_rules = template_data["rules"]
            
            # 更新支持的后缀
            default_extensions = [".pdf", ".doc", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"]
            raw_extensions = template_data.get("supported_extensions", default_extensions)
            self.supported_extensions = [ext.lower() for ext in raw_extensions]
            return True
        return False
    
    def display_templates(self):
        """显示所有可用模板的信息"""
        print("可用的文件识别模板:")
        print("=" * 80)

        for i, (template_key, template_info) in enumerate(self.templates.items(), 1):
            current_marker = " [当前使用]" if template_key == self.current_template else ""
            print(f"{i}. {template_info['name']}{current_marker}")
            print(f"   描述: {template_info['description']}")
            print(f"   文件类型数: {len(template_info['rules'])}")

            # 显示该模板支持的文件扩展名
            default_exts = ['.pdf', '.doc', '.docx', '.xlsx', '.png', '.jpg', '.jpeg']
            extensions = template_info.get('supported_extensions', default_exts)
            print(f"   支持格式: {', '.join(extensions[:5])}")
            if len(extensions) > 5:
                print(f"                等{len(extensions)}种格式")
            else:
                print()

            # 显示该模板的文件类型
            file_types = list(template_info['rules'].keys())
            print(f"   包含类型: {', '.join(file_types[:3])}")
            if len(file_types) > 3:
                print(f"                {'等' + str(len(file_types)) + '种文件类型'}")
            print()
        
        return list(self.templates.keys())

    def find_target_files(self, base_folder):
        """
        在材料包文件夹中查找目标文件
        先递归遍历找到模板指定的文件夹，再在这些文件夹中查找文件
        """
        found_files = {}
        
        for file_type, rules in self.file_rules.items():
            found_files[file_type] = []
        
        # 递归遍历所有子文件夹，找到模板指定的文件夹
        for root, dirs, files in os.walk(base_folder):
            current_folder_name = os.path.basename(root)
            
            # 检查当前文件夹是否匹配任何规则中的指定文件夹
            for file_type, rules in self.file_rules.items():
                target_folders = rules.get("folders", [])
                
                # 检查当前文件夹名是否在目标文件夹列表中
                folder_matched = False
                for target_folder in target_folders:
                    if not target_folder or target_folder == ".":
                        continue
                    # 支持部分匹配（文件夹名包含目标名称）
                    if target_folder in current_folder_name or current_folder_name == target_folder:
                        folder_matched = True
                        break
                
                if folder_matched:
                    # 在匹配的文件夹中查找符合关键词的文件
                    self._search_files_in_folder(
                        root, current_folder_name, file_type, rules, found_files
                    )
        
        # 同时在根目录查找（扁平结构）
        for file_type, rules in self.file_rules.items():
            target_folders = rules.get("folders", [])
            if "" in target_folders or "." in target_folders:
                self._search_files_in_folder(
                    base_folder, "", file_type, rules, found_files
                )
        
        return found_files
    
    def _search_files_in_folder(self, folder_path, folder_name, file_type, rules, found_files):
        """
        在指定文件夹中搜索符合规则的文件
        """
        try:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                
                # 处理模板中支持的文件类型
                if (file.lower().endswith(tuple(self.supported_extensions)) and
                    os.path.isfile(file_path)):
                    
                    # 检查是否已经添加了标签（任何标签）
                    if '#' in file:
                        continue  # 跳过已经有标签的文件
                    
                    # 检查文件名是否包含关键词
                    file_matched = False
                    for keyword in rules["keywords"]:
                        if keyword in file:
                            file_matched = True
                            break
                    
                    if file_matched:
                        # 检查是否已经添加过相同文件（避免重复）
                        already_added = any(
                            existing['path'] == file_path 
                            for existing in found_files[file_type]
                        )
                        
                        if not already_added:
                            relative_path = os.path.join(folder_name, file) if folder_name else file
                            found_files[file_type].append({
                                'path': file_path,
                                'folder': folder_name or "根目录",
                                'filename': file,
                                'relative_path': relative_path
                            })
        except Exception as e:
            # 忽略文件夹访问错误
            pass
    
    def generate_new_name(self, file_info, file_type):
        """
        生成新的文件名
        """
        original_name = file_info['filename']
        
        # 为所有文件添加标签
        name_without_ext = Path(original_name).stem
        extension = Path(original_name).suffix
        tag = self.file_rules[file_type]["tag"]
        
        return f"{name_without_ext}{tag}{extension}"
    
    def rename_files(self, base_folder):
        """
        执行文件重命名
        """
        print(f"🔍 正在分析文件夹: {os.path.basename(base_folder)}")
        print("=" * 80)
        
        # 查找目标文件
        found_files = self.find_target_files(base_folder)
        
        # 显示找到的文件
        total_files = 0
        for file_type, files in found_files.items():
            if files:
                print(f"\n📁 {file_type}:")
                for file_info in files:
                    print(f"  📄 {file_info['relative_path']}")
                    total_files += 1
            else:
                print(f"\n❌ 未找到: {file_type}")
        
        if total_files == 0:
            print("\n⚠️  没有找到需要重命名的文件")
            return False
        
        print(f"\n📊 总共找到 {total_files} 个文件需要重命名")
        
        # 确认操作
        confirm = input(f"\n确认对这些文件进行重命名吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            return False
        
        # 执行重命名
        print(f"\n🚀 开始重命名操作...")
        print("=" * 80)
        
        renamed_count = 0
        failed_count = 0
        skipped_count = 0
        
        for file_type, files in found_files.items():
            if not files:
                continue
                
            print(f"\n📁 处理 {file_type}:")
            
            for file_info in files:
                original_path = file_info['path']
                new_filename = self.generate_new_name(file_info, file_type)
                new_path = os.path.join(os.path.dirname(original_path), new_filename)
                
                print(f"  📄 {file_info['filename']}")
                print(f"     -> {new_filename}")
                
                # 检查新文件是否已存在
                if os.path.exists(new_path):
                    print(f"     ⏭️  目标文件已存在，跳过")
                    skipped_count += 1
                    continue
                
                try:
                    os.rename(original_path, new_path)
                    print(f"     ✅ 重命名成功")
                    renamed_count += 1
                except Exception as e:
                    print(f"     ❌ 重命名失败: {e}")
                    failed_count += 1
        
        # 显示统计结果
        print("\n" + "=" * 80)
        print("📊 重命名操作完成！统计结果:")
        print(f"  📄 目标文件数: {total_files}")
        print(f"  ✅ 成功重命名: {renamed_count}")
        print(f"  ❌ 重命名失败: {failed_count}")
        print(f"  ⏭️  跳过文件: {skipped_count}")
        
        return renamed_count > 0

def process_material_package(folder_path, template_name="牙科手机模板"):
    """
    处理单个材料包文件夹
    """
    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        return False
    
    if not os.path.isdir(folder_path):
        print(f"❌ 路径不是文件夹: {folder_path}")
        return False
    
    renamer = UniversalFileRenamer(template_name)
    return renamer.rename_files(folder_path)

def _get_folder_patterns_from_template(template_name=None):
    """从模板中获取文件夹匹配模式"""
    if template_name:
        # 尝试从模板获取模式
        template_path = get_resource_path(os.path.join("template", "data_read_templates", f"{template_name}.json"))
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                patterns = []
                # 材料包查找模板的格式是rules数组，每个rule有pattern和type字段
                rules = template_data.get('rules', [])
                for rule in rules:
                    if rule.get('type') == 'folder':
                        pattern = rule.get('pattern', '')
                        if pattern:
                            patterns.append(pattern)
                if patterns:
                    return patterns
            except Exception as e:
                print(f"⚠️  读取模板失败 {template_name}: {e}")

    # 默认模式
    return ["*材料包", "*_*_*", "*0010600*"]


def _match_folder_patterns(folder_name, patterns):
    """检查文件夹名是否匹配任一模式"""
    import fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(folder_name, pattern):
            return True
    return False


def scan_data_folder(template_name=None):
    """
    扫描data文件夹中的所有材料包文件夹
    适应三种结构：
    1. data/编号/ 直接包含分类文件夹（如：data/0010600120240919/）
    2. data/编号/编号_公司名_材料包/ 包含分类文件夹（如：data/0010600120240958/0010600120240958_盛丰医疗科技（深圳）有限公司_材料包/）
    3. data/编号_公司名_产品类型/ 扁平结构（文件直接在根目录）

    Args:
        template_name: 材料包查找模板名称，如果为None则使用默认规则
    """
    # 获取文件夹匹配模式
    folder_patterns = _get_folder_patterns_from_template(template_name)

    data_folder = get_app_path("data")
    material_packages = []

    if not os.path.exists(data_folder):
        print(f"❌ data文件夹不存在: {data_folder}")
        return []

    # 遍历data文件夹中的所有子文件夹
    for folder_name in os.listdir(data_folder):
        folder_path = os.path.join(data_folder, folder_name)

        # 检查是否是文件夹
        if os.path.isdir(folder_path):
            try:
                # 使用模板规则或默认规则检查文件夹
                if _match_folder_patterns(folder_name, folder_patterns):
                    # 如果文件夹名匹配规则，进一步检查是否包含医疗器械结构
                    if has_medical_device_structure(folder_path):
                        material_packages.append(folder_path)
                    else:
                        # 如果不检查结构，直接添加（适用于简单的文件夹名匹配）
                        material_packages.append(folder_path)

                # 无论是否匹配，都需要检查子文件夹（因为材料包可能在嵌套目录中）
                try:
                    for sub_folder_name in os.listdir(folder_path):
                        sub_folder_path = os.path.join(folder_path, sub_folder_name)

                        if os.path.isdir(sub_folder_path):
                            # 检查子文件夹是否是材料包
                            if (_match_folder_patterns(sub_folder_name, folder_patterns) or
                                has_medical_device_structure(sub_folder_path)):
                                material_packages.append(sub_folder_path)
                except (PermissionError, OSError):
                    # 如果无法访问子文件夹，跳过
                    pass
                    
            except PermissionError:
                # 跳过无权限访问的文件夹
                print(f"⚠️  跳过无权限访问的文件夹: {folder_path}")
                continue
            except Exception as e:
                # 跳过其他错误的文件夹
                print(f"⚠️  跳过错误文件夹 {folder_path}: {e}")
                continue
    
    return sorted(material_packages)

def has_medical_device_structure(folder_path):
    """
    检查文件夹是否具有医疗器械材料包的文件夹结构
    """
    try:
        subfolders = [item for item in os.listdir(folder_path) 
                     if os.path.isdir(os.path.join(folder_path, item))]
        
        # 检查是否包含典型的医疗器械申报文件夹
        medical_indicators = [
            "1.监管信息-1.2申请表",
            "1.监管信息-1.4产品列表", 
            "2.综述资料-2.3产品描述",
            "3.非临床资料-3.4产品技术要求及检验报告",
            "5.产品说明书和标签样稿-5.2产品说明书",
            "7.营业执照"
        ]
        
        # 如果包含至少2个典型文件夹，认为是医疗器械材料包
        found_indicators = sum(1 for indicator in medical_indicators 
                             if indicator in subfolders)
        
        return found_indicators >= 2
        
    except Exception:
        return False

def batch_process_all_data(template_name="牙科手机模板", gui_mode=False, confirmation_callback=None, material_package_template=None):
    """
    批量处理data文件夹中的所有材料包文件夹
    参数:
        template_name: 模板名称
        gui_mode: 是否为GUI模式
        confirmation_callback: GUI模式下的确认回调函数
        material_package_template: 材料包查找模板名称
    """
    print("🔍 正在扫描data文件夹中的材料包文件夹...")
    if material_package_template:
        print(f"📦 使用材料包查找规则: {material_package_template}")
        material_packages = scan_data_folder(material_package_template)
    else:
        print("📦 使用默认规则扫描材料包")
        material_packages = scan_data_folder()
    
    if not material_packages:
        print("❌ 在data文件夹中没有找到任何材料包文件夹")
        return False
    
    print(f"📊 找到 {len(material_packages)} 个材料包文件夹:")
    for i, package in enumerate(material_packages, 1):
        # 显示从data开始的相对路径，但突出显示材料包名称
        relative_path = os.path.relpath(package, "data")
        package_name = os.path.basename(package)
        print(f"  {i:2d}. {relative_path}")
        print(f"      📦 {package_name}")
    
    # 显示将要使用的模板
    renamer = UniversalFileRenamer(template_name)
    template_info = renamer.get_template_info(template_name)
    if template_info:
        print(f"\n🎯 将使用模板: {template_info['name']}")
        print(f"   📝 {template_info['description']}")
    else:
        print(f"\n⚠️  模板不存在: {template_name}，使用默认设置")
        template_info = {'name': template_name, 'description': '默认模板'}
    
    # 确认批量操作
    if not gui_mode:
        print(f"\n⚠️  即将对以上所有材料包文件夹执行重命名操作")
        confirm = input("确认继续批量处理吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            return False
    else:
        # GUI模式下的确认
        if confirmation_callback:
            message = f"找到 {len(material_packages)} 个材料包文件夹，即将使用模板「{template_info['name']}」进行批量重命名：\n\n"
            for i, package in enumerate(material_packages[:10], 1):  # 最多显示10个
                relative_path = os.path.relpath(package, "data")
                package_name = os.path.basename(package)
                message += f"{i:2d}. {package_name}\n"
            if len(material_packages) > 10:
                message += f"\n... 还有 {len(material_packages) - 10} 个材料包\n"
            message += f"\n模板: {template_info['description']}\n\n重命名操作将为所有对应文件添加识别标签。\n\n是否继续？"
            
            if not confirmation_callback("确认批量重命名", message):
                print("❌ 用户取消了操作")
                return False

    # 统计信息
    total_packages = len(material_packages)
    success_count = 0
    processed_files = 0
    
    print(f"\n🚀 开始批量处理...")
    print("=" * 80)
    
    # 处理每个材料包文件夹
    for i, package in enumerate(material_packages, 1):
        package_name = os.path.basename(package)
        print(f"\n📁 [{i}/{total_packages}] 处理: {package_name}")
        print("-" * 60)
        
        try:
            renamer_instance = UniversalFileRenamer(template_name)
            
            # 查找目标文件（不执行重命名，只统计）
            found_files = renamer_instance.find_target_files(package)
            
            package_file_count = sum(len(files) for files in found_files.values())
            if package_file_count == 0:
                print("⚠️  没有找到需要重命名的文件")
                continue
            
            print(f"📊 找到 {package_file_count} 个文件需要重命名")
            
            # 执行重命名（静默模式）
            renamed_count = 0
            skipped_count = 0
            failed_count = 0
            
            for file_type, files in found_files.items():
                if not files:
                    continue
                
                for file_info in files:
                    original_path = file_info['path']
                    new_filename = renamer_instance.generate_new_name(file_info, file_type)
                    new_path = os.path.join(os.path.dirname(original_path), new_filename)
                    
                    # 检查新文件是否已存在
                    if os.path.exists(new_path):
                        print(f"  ⏭️  跳过 {file_type}: 文件已存在标签")
                        skipped_count += 1
                        continue
                    
                    try:
                        os.rename(original_path, new_path)
                        print(f"  ✅ 重命名 {file_type}: {os.path.basename(new_filename)}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"  ❌ 失败 {file_type}: {e}")
                        failed_count += 1
            
            if renamed_count > 0:
                success_count += 1
                processed_files += renamed_count
            
            print(f"  📊 本文件夹结果: 成功{renamed_count} 跳过{skipped_count} 失败{failed_count}")
            
        except Exception as e:
            print(f"  ❌ 处理文件夹时出错: {e}")
        
        # 添加分隔线
        if i < total_packages:
            print()
    
    # 显示最终统计结果
    print("\n" + "=" * 80)
    print("📊 批量处理完成！最终统计:")
    print(f"  📁 总材料包数: {total_packages}")
    print(f"  ✅ 成功处理数: {success_count}")
    print(f"  ❌ 跳过数: {total_packages - success_count}")
    print(f"  📄 总重命名文件数: {processed_files}")
    print(f"  📈 处理成功率: {(success_count / total_packages * 100):.1f}%")
    
    return success_count > 0

def select_template():
    """
    选择文件识别模板
    """
    renamer = UniversalFileRenamer()
    available_templates = renamer.display_templates()
    
    try:
        choice = input(f"\n请选择模板 (1-{len(available_templates)}) [默认: 1]: ").strip()
        
        if not choice:
            choice = "1"
        
        template_index = int(choice) - 1
        if 0 <= template_index < len(available_templates):
            selected_template = available_templates[template_index]
            return selected_template
        else:
            print("❌ 无效选择，使用默认牙科手机模板")
            return "牙科手机模板"
    
    except ValueError:
        print("❌ 输入无效，使用默认牙科手机模板")
        return "牙科手机模板"

def main():
    print("🏷️  通用文件重命名工具 (多模板版)")
    print("=" * 80)
    print("功能：为材料包文件夹中的指定文件添加标识标签")
    print("特色：支持多种医疗器械类型的专用文件识别模板")
    print("扫描路径：data/编号_公司名_产品类型/ （支持分类结构和扁平结构）")
    print("自动识别：基于文件夹名称(编号0010600开头)或医疗器械文件夹结构")
    print("=" * 80)
    
    # 选择模板
    print("\n🎯 步骤1: 选择文件识别模板")
    selected_template = select_template()
    
    # 扫描可用的材料包文件夹
    print(f"\n🔍 步骤2: 正在扫描data文件夹...")
    material_packages = scan_data_folder()
    
    if not material_packages:
        print("❌ 在data文件夹中没有找到任何材料包文件夹")
        return
    
    print(f"📂 检测到 {len(material_packages)} 个材料包文件夹")
    
    print(f"\n📝 步骤3: 选择处理模式:")
    print(f"  1. 批量处理所有材料包文件夹")
    print(f"  2. 选择特定文件夹进行处理")
    
    try:
        choice = input(f"\n请输入选择 (1-2): ").strip()
        
        if choice == "1":
            # 批量处理所有文件夹
            success = batch_process_all_data(selected_template)
            if success:
                print(f"\n🎉 批量处理完成!")
            else:
                print(f"\n💥 批量处理未成功!")
        
        elif choice == "2":
            # 显示文件夹列表供选择
            print(f"\n📂 可用的材料包文件夹:")
            for i, package in enumerate(material_packages, 1):
                relative_path = os.path.relpath(package, "data")
                package_name = os.path.basename(package)
                print(f"  {i:2d}. {relative_path}")
                print(f"      📦 {package_name}")
            
            folder_choice = input(f"\n请选择文件夹 (1-{len(material_packages)}): ").strip()
            folder_index = int(folder_choice) - 1
            
            if 0 <= folder_index < len(material_packages):
                selected_folder = material_packages[folder_index]
                success = process_material_package(selected_folder, selected_template)
                if success:
                    print(f"\n🎉 重命名操作完成!")
                else:
                    print(f"\n💥 重命名操作未成功!")
            else:
                print("❌ 无效选择")
        
        else:
            print("❌ 无效选择")
    
    except ValueError:
        print("❌ 请输入有效数字")
    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")

if __name__ == "__main__":
    main()
