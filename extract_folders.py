#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹提取工具
基于JSON模板从ZIP包中提取和整理文件夹结构
用于医疗器械文档处理流程的文档分类整理

作者：Lxx   
更新时间：2025-10-15
"""

import os
import sys
import shutil
import re
import json
from pathlib import Path

from path_helper import get_resource_path, get_app_path


class FolderExtractor:
    def __init__(self, template_name="通用模板"):
        self.output_folder = "output"
        self.template_folder = get_resource_path(os.path.join("template", "folder_templates"))

        # 初始化模板字典
        self.templates = {}

        # 加载JSON模板
        self._load_json_templates()
        
        # 设置当前使用的模板
        self.current_template = template_name
        if template_name not in self.templates:
            print(f"⚠️  模板 '{template_name}' 不存在，使用默认通用模板")
            self.current_template = "通用模板"
        self.extraction_rules = self.templates[self.current_template]["rules"]
    
    def _load_json_templates(self):
        """从JSON文件加载提取模板"""
        if not os.path.exists(self.template_folder):
            return
        
        try:
            for file_name in os.listdir(self.template_folder):
                if file_name.endswith('.json'):
                    file_path = os.path.join(self.template_folder, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        
                        # 验证模板格式
                        if self._validate_extraction_template(template_data, file_name):
                            template_key = file_name[:-5]  # 移除.json扩展名
                            self.templates[template_key] = template_data
                    
                    except (json.JSONDecodeError, Exception):
                        # 静默跳过无效文件
                        continue
        except Exception:
            # 静默跳过文件夹访问错误
            pass
    
    def _validate_extraction_template(self, template_data, file_name):
        """验证提取模板数据格式"""
        required_fields = ['name', 'description', 'rules']

        # 检查必需字段
        for field in required_fields:
            if field not in template_data:
                return False

        # 检查rules格式
        if not isinstance(template_data['rules'], dict) or not template_data['rules']:
            return False

        # 检查每个规则
        for rule_name, rule_data in template_data['rules'].items():
            if not isinstance(rule_data, list):
                return False

        return True
    
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
            self.extraction_rules = self.templates[template_name]["rules"]
            return True
        return False
    
    def display_templates(self):
        """显示所有可用模板的信息"""
        print("📋 可用的文件夹提取模板:")
        print("=" * 80)
        
        for i, (template_key, template_info) in enumerate(self.templates.items(), 1):
            current_marker = " [当前使用]" if template_key == self.current_template else ""
            print(f"{i}. {template_info['name']}{current_marker}")
            print(f"   📝 {template_info['description']}")
            print(f"   📁 文件夹类型数: {len(template_info['rules'])}")
            
            # 显示该模板的文件夹类型
            folder_types = list(template_info['rules'].keys())
            print(f"   📂 包含类型: {', '.join(folder_types[:3])}")
            if len(folder_types) > 3:
                print(f"                {'等' + str(len(folder_types)) + '种文件夹类型'}")
            print()
        
        return list(self.templates.keys())
    
    def get_target_folders(self):
        """
        获取要提取的目标文件夹列表
        """
        target_folders = set()
        for folders in self.extraction_rules.values():
            target_folders.update(folders)
        return sorted(list(target_folders))
    
    def check_available_folders(self, source_folder):
        """
        检查源文件夹中哪些目标文件夹存在
        """
        target_folders = self.get_target_folders()
        available_folders = []
        
        for folder_name in target_folders:
            source_folder_path = os.path.join(source_folder, folder_name)
            if os.path.exists(source_folder_path):
                available_folders.append(folder_name)
        
        return available_folders
    
    def create_output_structure(self, material_package_name, available_folders):
        """
        在output文件夹中创建目录结构
        """
        # 创建主输出文件夹（不删除已存在的内容）
        os.makedirs(self.output_folder, exist_ok=True)
        
        # 创建材料包主文件夹
        main_output_folder = os.path.join(self.output_folder, material_package_name)
        
        # 如果材料包文件夹已存在，删除它以重新创建
        if os.path.exists(main_output_folder):
            print(f"⚠️  材料包文件夹已存在，将重新创建: {material_package_name}")
            shutil.rmtree(main_output_folder)
        
        os.makedirs(main_output_folder, exist_ok=True)
        
        # 只为存在的文件夹创建目录
        for folder_name in available_folders:
            folder_path = os.path.join(main_output_folder, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            print(f"📁 创建文件夹: {folder_name}")
        
        return main_output_folder
    
    def copy_folders(self, source_folder, available_folders, output_main_folder):
        """
        复制整个文件夹到输出文件夹
        """
        if not os.path.exists(source_folder):
            print(f"❌ 源文件夹不存在: {source_folder}")
            return False
        
        total_folders = len(available_folders)
        copied_count = 0
        failed_count = 0
        total_files = 0
        
        print(f"\n🚀 开始复制文件夹...")
        print("=" * 80)
        
        for folder_name in available_folders:
            print(f"\n📁 处理文件夹: {folder_name}")
            
            source_folder_path = os.path.join(source_folder, folder_name)
            output_folder_path = os.path.join(output_main_folder, folder_name)
            
            try:
                # 复制整个文件夹及其所有内容
                if os.path.exists(output_folder_path):
                    shutil.rmtree(output_folder_path)
                
                shutil.copytree(source_folder_path, output_folder_path)
                
                # 统计复制的文件数量
                folder_file_count = sum([len(files) for r, d, files in os.walk(output_folder_path)])
                total_files += folder_file_count
                copied_count += 1
                
                print(f"  ✅ 复制成功: {folder_name} ({folder_file_count} 个文件)")
                
            except Exception as e:
                failed_count += 1
                print(f"  ❌ 复制失败: {folder_name} - {e}")
        
        # 显示统计结果
        print("\n" + "=" * 80)
        print("📊 文件夹复制完成！统计结果:")
        print(f"  📁 可用文件夹数: {total_folders}")
        print(f"  ✅ 成功复制: {copied_count}")
        print(f"  ❌ 复制失败: {failed_count}")
        print(f"  📄 总复制文件数: {total_files}")
        if total_folders > 0:
            print(f"  📈 成功率: {(copied_count / total_folders * 100):.1f}%")
        
        return copied_count > 0
    
    def extract_folders(self, source_folder):
        """
        执行文件夹提取操作
        """
        material_package_name = os.path.basename(source_folder)
        
        print("📂 文件夹提取工具")
        print("=" * 80)
        print(f"源文件夹: {source_folder}")
        print(f"输出文件夹: {self.output_folder}")
        print(f"材料包名称: {material_package_name}")
        print("=" * 80)
        
        # 检查哪些目标文件夹存在
        available_folders = self.check_available_folders(source_folder)
        
        if not available_folders:
            print(f"\n⏭️  在材料包中没有找到任何符合提取规则的文件夹，跳过处理")
            return False
        
        print(f"\n📊 提取规则:")
        print(f"  📁 可用文件夹数: {len(available_folders)}")
        print("  📁 要提取的文件夹:")
        for i, folder in enumerate(available_folders, 1):
            print(f"    {i:2d}. {folder}")
        
        # 自动确认操作
        print(f"\n✅ 自动确认执行提取操作")
        
        # 创建输出目录结构
        print(f"\n📁 创建输出目录结构...")
        output_main_folder = self.create_output_structure(material_package_name, available_folders)
        
        # 复制文件夹
        success = self.copy_folders(source_folder, available_folders, output_main_folder)
        
        if success:
            print(f"\n🎉 提取操作完成！")
            print(f"📁 输出位置: {os.path.abspath(self.output_folder)}")
        else:
            print(f"\n💥 提取操作失败！")
        
        return success

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


def scan_material_packages(template_name=None):
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
        print(f"⚠️  data文件夹不存在: {data_folder}")
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

                # 如果文件夹名不匹配，但可能是编号文件夹，需要进一步检查子文件夹
                elif folder_name.startswith("0010600"):
                    # 遍历编号文件夹下的子文件夹
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

def select_extraction_template():
    """
    选择文件夹提取模板
    """
    extractor = FolderExtractor()
    available_templates = extractor.display_templates()
    
    try:
        choice = input(f"\n请选择模板 (1-{len(available_templates)}) [默认: 1]: ").strip()
        
        if not choice:
            choice = "1"
        
        template_index = int(choice) - 1
        if 0 <= template_index < len(available_templates):
            selected_template = available_templates[template_index]
            return selected_template
        else:
            print("❌ 无效选择，使用默认通用模板")
            return "通用模板"
    
    except ValueError:
        print("❌ 输入无效，使用默认通用模板")
        return "通用模板"

def main():
    print("📂 通用材料包文件夹提取工具 (多模板版)")
    print("=" * 80)
    print("功能：根据预定义规则提取指定文件夹到output目录")
    print("特色：支持多种医疗器械类型的专用文件夹提取模板")
    print("扫描路径：data/编号文件夹/*_材料包/ （遍历两层文件夹）")
    print("=" * 80)
    
    # 选择模板
    print("\n🎯 步骤1: 选择文件夹提取模板")
    selected_template = select_extraction_template()
    
    # 扫描可用的材料包文件夹
    print(f"\n🔍 步骤2: 正在扫描data文件夹中的材料包...")
    material_packages = scan_material_packages()
    
    if not material_packages:
        print("⏭️  在data文件夹中没有找到任何材料包文件夹，程序结束")
        return
    
    print(f"📂 找到 {len(material_packages)} 个材料包文件夹:")
    for i, package in enumerate(material_packages, 1):
        # 显示从data开始的相对路径，但突出显示材料包名称
        relative_path = os.path.relpath(package, "data")
        package_name = os.path.basename(package)
        print(f"  {i:2d}. {relative_path}")
        print(f"      📦 {package_name}")
    
    # 选择处理模式
    print(f"\n📝 步骤3: 选择处理模式:")
    print(f"  1. 处理指定材料包")
    print(f"  2. 批量处理所有材料包")
    
    try:
        choice = input(f"\n请输入选择 (1-2): ").strip()
        
        extractor = FolderExtractor(selected_template)
        
        # 显示将要使用的模板
        template_info = extractor.get_template_info(selected_template)
        print(f"\n🎯 使用模板: {template_info['name']}")
        print(f"   📝 {template_info['description']}")
        
        if choice == "1":
            # 选择特定材料包
            folder_choice = input(f"\n请选择材料包 (1-{len(material_packages)}): ").strip()
            folder_index = int(folder_choice) - 1
            
            if 0 <= folder_index < len(material_packages):
                # 在单个处理开始前清空output文件夹
                if os.path.exists(extractor.output_folder):
                    print(f"🧹 清空输出文件夹: {extractor.output_folder}")
                    shutil.rmtree(extractor.output_folder)
                
                selected_package = material_packages[folder_index]
                success = extractor.extract_folders(selected_package)
                if success:
                    print(f"\n🎉 提取操作完成!")
                else:
                    print(f"\n💥 提取操作失败!")
            else:
                print("❌ 无效选择")
        
        elif choice == "2":
            # 批量处理所有材料包
            print(f"\n✅ 自动开始批量处理所有 {len(material_packages)} 个材料包")
            
            # 在批量处理开始前清空output文件夹
            if os.path.exists(extractor.output_folder):
                print(f"🧹 清空输出文件夹: {extractor.output_folder}")
                shutil.rmtree(extractor.output_folder)
            
            success_count = 0
            skipped_count = 0
            for i, package in enumerate(material_packages, 1):
                package_name = os.path.basename(package)
                print(f"\n{'='*80}")
                print(f"[{i}/{len(material_packages)}] 处理: {package_name}")
                print(f"{'='*80}")
                
                if extractor.extract_folders(package):
                    success_count += 1
                else:
                    skipped_count += 1
            
            print(f"\n🎉 批量处理完成！成功处理了 {success_count}/{len(material_packages)} 个材料包")
            if skipped_count > 0:
                print(f"⏭️  跳过了 {skipped_count} 个材料包（没有符合提取规则的文件夹）")
        
        else:
            print("❌ 无效选择")
    
    except ValueError:
        print("❌ 请输入有效数字")
    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")

if __name__ == "__main__":
    main()
