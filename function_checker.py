#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能检查器 - 专门用于检查各个功能模块的可用性

作者：Lxx   
更新时间：2025-09-25
"""

import os
import sys
import json
import zipfile
import traceback
from pathlib import Path

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和打包后的exe环境"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下使用当前工作目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class FunctionChecker:
    """功能检查器类"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or print
        self.check_results = {}
    
    def log(self, message):
        """记录日志"""
        if self.log_callback:
            # 确保消息是字符串类型，避免编码问题
            if isinstance(message, str):
                self.log_callback(message)
            else:
                self.log_callback(str(message))
    
    def check_python_environment(self):
        """检查Python环境"""
        self.log("检查Python环境...")
        
        try:
            # 检查Python版本
            version = sys.version_info
            if version.major >= 3 and version.minor >= 7:
                self.log(f"  Python版本: {version.major}.{version.minor}.{version.micro}")
                return True
            else:
                self.log(f"  Python版本过低: {version.major}.{version.minor}.{version.micro} (需要≥3.7)")
                return False
        except Exception as e:
            self.log(f"  Python环境检查失败: {e}")
            return False
    
    def check_required_modules(self):
        """检查必需的Python模块"""
        self.log("检查必需模块...")
        
        required_modules = [
            ("tkinter", "GUI界面"),
            ("pathlib", "路径处理"),
            ("zipfile", "ZIP文件处理"),
            ("json", "JSON数据处理"),
            ("threading", "多线程"),
            ("queue", "队列"),
            ("shutil", "文件操作"),
            ("os", "系统操作"),
            ("re", "正则表达式")
        ]
        
        failed_modules = []
        
        for module_name, description in required_modules:
            try:
                __import__(module_name)
                self.log(f"  {module_name} - {description}")
            except ImportError as e:
                self.log(f"  {module_name} - {description}: {e}")
                failed_modules.append(module_name)
        
        return len(failed_modules) == 0
    
    def check_optional_modules(self):
        """检查可选模块"""
        self.log("检查可选模块...")

        optional_modules = [
            ("win32com.client", "Word转PDF功能", "pywin32"),
            ("PyInstaller", "exe打包功能", "pyinstaller")
        ]

        # 可选模块检查总是通过的，只显示信息
        for module_name, description, package_name in optional_modules:
            try:
                __import__(module_name)
                self.log(f"  {module_name} - {description}")
            except ImportError:
                self.log(f"   {module_name} - {description}: 未安装 (pip install {package_name})")

        # 可选模块检查总是返回True，因为这些模块是可选的
        return True
    
    def check_project_modules(self):
        """检查项目模块"""
        self.log("检查项目模块...")
        
        project_modules = [
            ("analyze_zip_encoding", "ZIP文件解压"),
            ("clean_folder", "文件夹清理"),
            ("extract_folders", "文件夹提取"),
            ("final_word_to_pdf", "Word转PDF"),
            ("universal_rename", "文件重命名")
        ]
        
        failed_modules = []
        
        for module_name, description in project_modules:
            try:
                __import__(module_name)
                self.log(f"  {module_name} - {description}")
            except ImportError as e:
                self.log(f"  {module_name} - {description}: {e}")
                failed_modules.append(module_name)
            except Exception as e:
                self.log(f"   {module_name} - {description}: {e}")
        
        return len(failed_modules) == 0
    
    def check_directory_structure(self):
        """检查目录结构"""
        self.log("检查目录结构...")
        
        required_dirs = [
            ("template/folder_templates", "文件夹提取模板", True),
            ("template/rename_templates", "文件重命名模板", True)
        ]
        
        optional_dirs = [
            ("data", "输入数据文件夹", False),
            ("output", "输出结果文件夹", False)
        ]
        
        missing_required = []
        
        # 检查必需目录
        for dir_name, description, required in required_dirs:
            # 使用get_resource_path获取正确的路径
            dir_path = get_resource_path(dir_name)
            if os.path.exists(dir_path):
                self.log(f"  {dir_name}/ - {description}")
            else:
                if required:
                    self.log(f"  {dir_name}/ - {description} (必需)")
                    missing_required.append(dir_name)
                else:
                    self.log(f"   {dir_name}/ - {description} (缺失)")
        
        # 检查可选目录
        for dir_name, description, required in optional_dirs:
            # 使用get_resource_path获取正确的路径
            dir_path = get_resource_path(dir_name)
            if os.path.exists(dir_path):
                self.log(f"  {dir_name}/ - {description}")
            else:
                self.log(f"  ℹ️  {dir_name}/ - {description} (运行时自动创建)")
        
        return len(missing_required) == 0
    
    def check_template_files(self):
        """检查模板文件"""
        self.log("检查模板文件...")
        
        template_dirs = ["template/folder_templates", "template/rename_templates"]
        all_valid = True
        
        for template_dir in template_dirs:
            # 使用get_resource_path获取正确的路径
            template_dir_path = get_resource_path(template_dir)
            if not os.path.exists(template_dir_path):
                self.log(f"  {template_dir}/ 目录不存在")
                all_valid = False
                continue
            
            json_files = [f for f in os.listdir(template_dir_path) if f.endswith('.json')]
            
            if not json_files:
                self.log(f"   {template_dir}/: 没有找到JSON模板文件")
                continue
            
            self.log(f"  {template_dir}/:")
            
            for json_file in json_files:
                file_path = os.path.join(template_dir_path, json_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 验证模板格式
                    if self._validate_template_format(data, template_dir):
                        self.log(f"    {json_file}")
                    else:
                        self.log(f"    {json_file} - 格式不正确")
                        all_valid = False
                        
                except json.JSONDecodeError as e:
                    self.log(f"    {json_file} - JSON格式错误: {e}")
                    all_valid = False
                except Exception as e:
                    self.log(f"    {json_file} - 读取失败: {e}")
                    all_valid = False
        
        return all_valid
    
    def _validate_template_format(self, data, template_type):
        """验证模板格式"""
        try:
            # 检查基本字段
            if not all(key in data for key in ['name', 'description', 'rules']):
                return False
            
            # 检查rules格式
            if not isinstance(data['rules'], dict):
                return False
            
            # 根据模板类型检查特定格式
            if template_type == "template/folder_templates":
                # 文件夹提取模板: rules中应该是字符串列表
                for key, value in data['rules'].items():
                    if not isinstance(value, list):
                        return False
            elif template_type == "template/rename_templates":
                # 重命名模板: rules中应该是字典
                for key, value in data['rules'].items():
                    if not isinstance(value, dict):
                        return False
                    if not all(subkey in value for subkey in ['folders', 'keywords', 'tag']):
                        return False
            
            return True
        except Exception:
            return False
    
    def check_data_folder_samples(self):
        """检查data文件夹中的示例数据"""
        self.log("检查data文件夹内容...")
        
        data_dir = Path("data")
        
        if not data_dir.exists():
            self.log("  ℹ️  data文件夹不存在，将在运行时创建")
            return True
        
        # 统计文件类型
        zip_files = list(data_dir.glob("*.zip"))
        folders = [item for item in data_dir.iterdir() if item.is_dir()]
        other_files = [item for item in data_dir.iterdir() if item.is_file() and not item.name.endswith('.zip')]
        
        self.log(f"  统计信息:")
        self.log(f"    ZIP文件: {len(zip_files)} 个")
        self.log(f"    文件夹: {len(folders)} 个")
        self.log(f"    其他文件: {len(other_files)} 个")
        
        # 检查是否有标准编号格式的文件夹
        standard_folders = [f for f in folders if f.name.startswith("0010600")]
        if standard_folders:
            self.log(f"  发现 {len(standard_folders)} 个标准申报文件夹")
            for folder in standard_folders[:3]:  # 只显示前3个
                self.log(f"    {folder.name}")
            if len(standard_folders) > 3:
                self.log(f"    ... 还有 {len(standard_folders) - 3} 个文件夹")
        
        return True
    
    def check_function_zip_extraction(self):
        """检查ZIP解压功能"""
        self.log("检查ZIP解压功能...")

        try:
            # 检查analyze_zip_encoding模块
            import analyze_zip_encoding

            # 检查关键函数是否存在
            if hasattr(analyze_zip_encoding, 'unzip_files_in_data_folder'):
                self.log("  ZIP解压函数可用")
            else:
                self.log("  ZIP解压函数不存在")
                return False

            # 检查编码处理函数
            if hasattr(analyze_zip_encoding, 'unzip_fix_encoding'):
                self.log("  中文编码处理函数可用")
            else:
                self.log("  中文编码处理函数不存在")
                return False

            return True

        except ImportError as e:
            self.log(f"  ZIP解压模块导入失败: {e}")
            return False
        except Exception as e:
            self.log(f"  ZIP解压功能检查失败: {e}")
            return False
    
    def check_function_folder_cleaning(self):
        """检查文件夹清理功能"""
        self.log("检查文件夹清理功能...")
        
        try:
            import clean_folder
            
            if hasattr(clean_folder, 'clean_folder'):
                self.log("  文件夹清理函数可用")
            else:
                self.log("  文件夹清理函数不存在")
                return False
            
            if hasattr(clean_folder, 'process_data_folders'):
                self.log("  批量处理函数可用")
            else:
                self.log("  批量处理函数不存在")
                return False
            
            return True
            
        except ImportError as e:
            self.log(f"  文件夹清理模块导入失败: {e}")
            return False
        except Exception as e:
            self.log(f"  文件夹清理功能检查失败: {e}")
            return False
    
    def check_function_folder_extraction(self):
        """检查文件夹提取功能"""
        self.log("检查文件夹提取功能...")
        
        try:
            import extract_folders
            
            if hasattr(extract_folders, 'FolderExtractor'):
                self.log("  文件夹提取器类可用")
            else:
                self.log("  文件夹提取器类不存在")
                return False
            
            if hasattr(extract_folders, 'scan_material_packages'):
                self.log("  材料包扫描函数可用")
            else:
                self.log("  材料包扫描函数不存在")
                return False
            
            return True
            
        except ImportError as e:
            self.log(f"  文件夹提取模块导入失败: {e}")
            return False
        except Exception as e:
            self.log(f"  文件夹提取功能检查失败: {e}")
            return False
    
    def check_function_word_to_pdf(self):
        """检查Word转PDF功能"""
        self.log("检查Word转PDF功能...")
        
        try:
            import final_word_to_pdf
            
            if hasattr(final_word_to_pdf, 'FinalWordToPDFConverter'):
                self.log("  Word转PDF转换器类可用")
            else:
                self.log("  Word转PDF转换器类不存在")
                return False
            
            if hasattr(final_word_to_pdf, 'batch_convert_data_folder'):
                self.log("  批量转换函数可用")
            else:
                self.log("  批量转换函数不存在")
                return False
            
            # 检查win32com是否可用
            try:
                import win32com.client
                self.log("  Microsoft Word COM接口可用")
            except ImportError:
                self.log("   Microsoft Word COM接口不可用 (需要安装pywin32)")
                self.log("     Word转PDF功能可能无法正常工作")
            
            return True
            
        except ImportError as e:
            self.log(f"  Word转PDF模块导入失败: {e}")
            return False
        except Exception as e:
            self.log(f"  Word转PDF功能检查失败: {e}")
            return False
    
    def check_function_file_renaming(self):
        """检查文件重命名功能"""
        self.log("检查文件重命名功能...")
        
        try:
            import universal_rename
            
            if hasattr(universal_rename, 'UniversalFileRenamer'):
                self.log("  文件重命名器类可用")
            else:
                self.log("  文件重命名器类不存在")
                return False
            
            if hasattr(universal_rename, 'batch_process_all_data'):
                self.log("  批量处理函数可用")
            else:
                self.log("  批量处理函数不存在")
                return False
            
            return True
            
        except ImportError as e:
            self.log(f"  文件重命名模块导入失败: {e}")
            return False
        except Exception as e:
            self.log(f"  文件重命名功能检查失败: {e}")
            return False
    
    def check_gui_functionality(self):
        """检查GUI功能"""
        self.log(" 检查GUI功能...")
        
        try:
            import tkinter as tk
            from tkinter import ttk, scrolledtext, messagebox, filedialog
            
            # 测试基本组件创建
            root = tk.Tk()
            root.withdraw()  # 隐藏窗口
            
            # 测试各种组件
            frame = ttk.Frame(root)
            button = ttk.Button(frame, text="测试")
            label = ttk.Label(frame, text="测试")
            text = scrolledtext.ScrolledText(frame)
            progress = ttk.Progressbar(frame)
            
            self.log("  Tkinter基本组件创建成功")
            
            root.destroy()
            
            # 检查主程序GUI模块
            import main_gui
            if hasattr(main_gui, 'MedicalDocProcessor'):
                self.log("  主程序GUI类可用")
            else:
                self.log("  主程序GUI类不存在")
                return False
            
            return True
            
        except ImportError as e:
            self.log(f"  GUI模块导入失败: {e}")
            return False
        except Exception as e:
            self.log(f"  GUI功能检查失败: {e}")
            return False
    
    def run_selective_check(self, selected_checks):
        """运行选择性检查"""
        self.log("开始选择性功能检查...")
        self.log("=" * 60)
        self.log(f"选中的棄查项目: {len(selected_checks)} 个")
        
        # 定义所有可用的检查项目
        all_checks = {
            "Python环境": self.check_python_environment,
            "必需模块": self.check_required_modules,
            "可选模块": self.check_optional_modules,
            "项目模块": self.check_project_modules,
            "目录结构": self.check_directory_structure,
            "模板文件": self.check_template_files,
            "数据文件夹": self.check_data_folder_samples,
            "公司材料包": self.check_company_package_structure,
            "ZIP解压功能": self.check_function_zip_extraction,
            "文件夹清理功能": self.check_function_folder_cleaning,
            "文件夹提取功能": self.check_function_folder_extraction,
            "Word转PDF功能": self.check_function_word_to_pdf,
            "文件重命名功能": self.check_function_file_renaming,
            "GUI功能": self.check_gui_functionality
        }
        
        # 统计信息
        passed_checks = 0
        total_checks = len(selected_checks)
        
        # 执行选中的检查
        for i, check_name in enumerate(selected_checks, 1):
            if check_name in all_checks:
                self.log(f"\n=== [{i}/{total_checks}] 检查 {check_name} ===")
                try:
                    result = all_checks[check_name]()
                    self.check_results[check_name] = result
                    if result:
                        passed_checks += 1
                        self.log(f"{check_name} 检查通过")
                    else:
                        self.log(f"{check_name} 检查未通过")
                except Exception as e:
                    self.log(f"{check_name} 检查失败: {e}")
                    self.check_results[check_name] = False
            else:
                self.log(f"\n 未知的检查项目: {check_name}")
        
        # 显示选择性检查结果
        self._display_selective_results(selected_checks, passed_checks, total_checks)
        
        return passed_checks == total_checks

    def check_company_package_structure(self, template_name=None):
        """检查公司材料包结构

        Args:
            template_name: 材料包查找模板名称，如果为None则使用默认规则
        """
        if template_name:
            self.log(f"使用模板: {template_name}")
        self.log("开始检查公司材料包结构...")

        try:
            # 尝试多个可能的数据文件夹路径
            possible_paths = [
                Path("data"),
                Path("./data"),
                Path(os.getcwd()) / "data"
            ]

            data_path = None
            for path in possible_paths:
                if path.exists() and path.is_dir():
                    data_path = path
                    break

            if not data_path:
                self.log("  未找到data文件夹")
                self.log("  请确保项目根目录下有data文件夹")
                return False

            self.log(f"  data文件夹存在: {data_path.absolute()}")

            # 获取文件夹匹配模式
            folder_patterns = self._get_folder_patterns(template_name)

            # 扫描公司材料包
            package_dirs = []
            try:
                # 先扫描一级目录
                for item in data_path.iterdir():
                    if item.is_dir():
                        dir_name = item.name
                        # 使用模板规则或默认规则匹配文件夹
                        if self._match_folder_patterns(dir_name, folder_patterns):
                            package_dirs.append((dir_name, item))

                # 如果一级目录没找到，再扫描二级目录
                if not package_dirs:
                    for item in data_path.iterdir():
                        if item.is_dir():
                            # 在每个子目录中查找材料包
                            for sub_item in item.iterdir():
                                if sub_item.is_dir():
                                    sub_dir_name = sub_item.name
                                    if self._match_folder_patterns(sub_dir_name, folder_patterns):
                                        package_dirs.append((sub_dir_name, sub_item))

            except Exception as e:
                self.log(f"  扫描data文件夹时出错: {e}")
                return False

            if not package_dirs:
                self.log("  未找到任何公司材料包")
                self.log("  请确保data文件夹下有格式为'编号_公司名称_材料包'的目录")
                self.log(f"  检查的路径: {data_path.absolute()}")

                # 显示找到的所有文件夹
                try:
                    all_dirs = [item.name for item in data_path.iterdir() if item.is_dir()]
                    if all_dirs:
                        self.log(f"  找到的文件夹: {', '.join(all_dirs[:5])}")
                        if len(all_dirs) > 5:
                            self.log(f"  ... 还有 {len(all_dirs) - 5} 个文件夹")
                    else:
                        self.log("  无文件夹")
                except Exception as e:
                    self.log(f"  无法读取文件夹内容: {e}")

                return False

            self.log(f"  发现 {len(package_dirs)} 个公司材料包")

            # 根据选择的模板来确定清理配置和检查规则
            clean_config = None
            required_folders = []
            critical_folders = []

            if template_name:
                # 显示模板信息
                self.log(f"  工具名称: 企业材料文档预处理工具")
                # 根据模板名称来确定检查规则（不读取模板文件内容）
                if "租赁金融报告" in template_name:
                    # 租赁金融报告模板的检查规则
                    clean_config_path = get_resource_path("template/clean_templates/clean.json")
                    if os.path.exists(clean_config_path):
                        with open(clean_config_path, 'r', encoding='utf-8') as f:
                            clean_config = json.load(f)
                    else:
                        # 如果没有专用配置，使用默认配置
                        clean_config_path = get_resource_path("template/clean_templates/clean_config.json")
                        with open(clean_config_path, 'r', encoding='utf-8') as f:
                            clean_config = json.load(f)

                    # 租赁金融报告需要的文件结构（检查文件而不是文件夹）
                    required_folders = [
                        "2022年审计",
                        "2023年三季度财务报表",
                        "营业执照",
                        "2021年审计"
                    ]
                    critical_folders = [
                        "2022年审计",
                        "营业执照"
                    ]
                elif "医疗器械" in template_name:
                    # 医疗器械模板的检查规则
                    clean_config_path = get_resource_path("template/clean_templates/clean_config.json")
                    with open(clean_config_path, 'r', encoding='utf-8') as f:
                        clean_config = json.load(f)

                    # 医疗器械申报文件夹结构
                    required_folders = [
                        "1.监管信息-1.2申请表",
                        "1.监管信息-1.4产品列表",
                        "2.综述资料-2.2概述",
                        "2.综述资料-2.3产品描述",
                        "3.非临床资料-3.4产品技术要求及检验报告",
                        "5.产品说明书和标签样稿-5.2产品说明书",
                        "7.营业执照"
                    ]
                    critical_folders = [
                        "1.监管信息-1.2申请表",
                        "1.监管信息-1.4产品列表",
                        "7.营业执照"
                    ]
                else:
                    # 默认使用医疗器械规则
                    clean_config_path = get_resource_path("template/clean_templates/clean_config.json")
                    with open(clean_config_path, 'r', encoding='utf-8') as f:
                        clean_config = json.load(f)

                    required_folders = [
                        "1.监管信息-1.2申请表",
                        "1.监管信息-1.4产品列表",
                        "2.综述资料-2.2概述",
                        "2.综述资料-2.3产品描述",
                        "3.非临床资料-3.4产品技术要求及检验报告",
                        "5.产品说明书和标签样稿-5.2产品说明书",
                        "7.营业执照"
                    ]
                    critical_folders = [
                        "1.监管信息-1.2申请表",
                        "1.监管信息-1.4产品列表",
                        "7.营业执照"
                    ]
            else:
                # 没有指定模板，使用默认配置
                clean_config_path = get_resource_path("template/clean_templates/clean_config.json")
                with open(clean_config_path, 'r', encoding='utf-8') as f:
                    clean_config = json.load(f)

                required_folders = [
                    "1.监管信息-1.2申请表",
                    "1.监管信息-1.4产品列表",
                    "2.综述资料-2.2概述",
                    "2.综述资料-2.3产品描述",
                    "3.非临床资料-3.4产品技术要求及检验报告",
                    "5.产品说明书和标签样稿-5.2产品说明书",
                    "7.营业执照"
                ]
                critical_folders = [
                    "1.监管信息-1.2申请表",
                    "1.监管信息-1.4产品列表",
                    "7.营业执照"
                ]

            self.log(f"  加载清理配置模板: {clean_config.get('name', '未知')}")

            # 检查每个材料包的结构
            all_passed = True
            for package_name, package_path in package_dirs:
                # 根据选择的模板显示正确的模板名称
                if template_name:
                    display_name = template_name
                else:
                    display_name = clean_config.get('name', '通用材料包')
                self.log(f"\n    检查材料包: {package_name} ({display_name})")

                missing_critical = []
                missing_other = []
                found_files = []
                found_folders = []

                # 根据模板名称确定检查类型
                check_files = False
                if template_name and "租赁金融报告" in template_name:
                    check_files = True  # 租赁金融报告检查文件
                else:
                    check_files = False  # 其他模板检查文件夹

                # 根据模板要求检查文件或文件夹
                if check_files:
                    # 租赁金融报告：检查文件
                    all_files = list(package_path.rglob('*'))
                    file_names = [f.name for f in all_files if f.is_file()]

                    for requirement in required_folders:
                        is_critical = requirement in critical_folders

                        # 文件检查
                        found = False
                        for file_name in file_names:
                            if requirement in file_name:
                                found = True
                                found_files.append(file_name)
                                break
                        if not found:
                            if is_critical:
                                missing_critical.append(requirement)
                            else:
                                missing_other.append(requirement)

                    # 显示找到的文件
                    if found_files:
                        self.log(f"      找到相关文件: {', '.join(set(found_files))}")
                else:
                    # 医疗器械和其他：检查文件夹
                    for folder in required_folders:
                        folder_path = package_path / folder
                        if not folder_path.exists():
                            if folder in critical_folders:
                                missing_critical.append(folder)
                            else:
                                missing_other.append(folder)
                        else:
                            found_folders.append(folder)
                            # 检查文件夹是否为空
                            try:
                                file_count = len(list(folder_path.rglob('*')))
                                if file_count == 0:
                                    self.log(f"       文件夹为空: {folder}")
                                else:
                                    self.log(f"      文件夹存在且有内容: {folder} ({file_count} 个文件)")
                            except Exception as e:
                                self.log(f"      检查文件夹时出错 {folder}: {e}")
                                missing_other.append(folder)

                    # 显示找到的文件夹
                    if found_folders:
                        self.log(f"      找到相关文件夹: {', '.join(found_folders)}")

                # 检查关键文件/文件夹
                if missing_critical:
                    # 根据模板名称动态显示消息
                    if check_files:
                        self.log(f"      缺少关键必需文件: {', '.join(missing_critical)}")
                    else:
                        self.log(f"      缺少关键必需文件夹: {', '.join(missing_critical)}")
                    all_passed = False
                else:
                    if check_files:
                        self.log("      关键必需文件都存在")
                    else:
                        self.log("      关键必需文件夹都存在")

                # 检查其他文件/文件夹（警告级别）
                if missing_other:
                    if check_files:
                        self.log(f"       缺少可选文件: {', '.join(missing_other)}")
                    else:
                        self.log(f"       缺少可选文件夹: {', '.join(missing_other)}")
                else:
                    if check_files:
                        self.log("      所有必需文件都存在")
                    else:
                        self.log("      所有必需文件夹都存在")

                # 显示当前使用的检查规则类型
                if template_name and "租赁金融报告" in template_name:
                    self.log("      检查租赁金融报告文件结构:")
                elif template_name and "医疗器械" in template_name:
                    self.log("      检查医疗器械申报文件结构:")
                else:
                    self.log("      检查通用文件结构:")

                # 使用清理配置检查文件类型
                rules = clean_config.get('rules', [])
                if rules:
                    self.log("      应用清理规则检查:")
                    for rule in rules:
                        pattern = rule.get('pattern', '')
                        rule_type = rule.get('type', '')
                        description = rule.get('description', '')

                        if rule_type == 'folder':
                            # 检查文件夹匹配规则
                            matching_dirs = []
                            for item in package_path.rglob('*'):
                                if item.is_dir() and Path(item.name).match(pattern):
                                    matching_dirs.append(str(item.relative_to(package_path)))

                            if matching_dirs:
                                self.log(f"        匹配规则 '{pattern}': {len(matching_dirs)} 个文件夹")
                            else:
                                self.log(f"         无文件夹匹配规则 '{pattern}'")

            if all_passed:
                if template_name and "租赁金融报告" in template_name:
                    self.log("  所有公司材料包租赁金融报告文件结构检查通过")
                elif template_name and "医疗器械" in template_name:
                    self.log("  所有公司材料包医疗器械申报文件结构检查通过")
                else:
                    self.log("  所有公司材料包结构检查通过")
            else:
                if check_files:
                    self.log("  部分材料包缺少关键必需文件")
                else:
                    self.log("  部分材料包缺少关键必需文件夹")

            return all_passed

        except Exception as e:
            self.log(f"  公司材料包检查失败: {e}")
            self.log(f"  详细错误: {traceback.format_exc()}")
            return False

    def _display_selective_results(self, selected_checks, passed_checks, total_checks):
        """显示选择性检查结果"""
        self.log("\n" + "=" * 60)
        self.log("选择性功能检查结果:")
        self.log(f"  选中检查项: {total_checks} 个")
        self.log(f"  通过检查: {passed_checks}/{total_checks}")
        self.log(f"  未通过检查: {total_checks - passed_checks}/{total_checks}")
        self.log(f"  📈 检查通过率: {(passed_checks / total_checks * 100):.1f}%")
        
        # 显示具体结果
        self.log("\n详细结果:")
        for check_name in selected_checks:
            if check_name in self.check_results:
                result = self.check_results[check_name]
                status = "通过" if result else "失败"
                self.log(f"  {status} {check_name}")
            else:
                self.log(f"   未执行 {check_name}")
        
        # 给出建议
        if passed_checks == total_checks:
            self.log("\n选中的所有功能检查通过！")
            if total_checks < 13:
                self.log("如需全面检查，建议运行完整检查。")
        else:
            failed_checks = [name for name in selected_checks 
                           if name in self.check_results and not self.check_results[name]]
            self.log("\n 部分检查未通过，请解决以下问题:")
            for failed_check in failed_checks:
                self.log(f"  • {failed_check}")
            
            self._provide_selective_suggestions(failed_checks)
    
    def _provide_selective_suggestions(self, failed_checks):
        """为选择性检查提供建议"""
        self.log("\n针对性解决建议:")
        
        suggestions = {
            "Python环境": ["• 更新到Python 3.7+版本"],
            "必需模块": ["• 安装缺失的Python包: pip install <包名>"],
            "可选模块": [
                "• 安装pywin32: pip install pywin32",
                "• 安装PyInstaller: pip install pyinstaller"
            ],
            "项目模块": ["• 检查项目文件是否完整且语法正确"],
            "目录结构": ["• 创建缺失的必需目录"],
            "模板文件": ["• 检查JSON模板文件格式是否正确"],
            "公司材料包": ["• 检查data文件夹下是否存在公司材料包", "• 确保材料包文件夹格式正确（编号_公司名称_材料包）"],
            "Word转PDF功能": [
                "• 安装Microsoft Word",
                "• 安装pywin32: pip install pywin32"
            ],
            "GUI功能": ["• 检查tkinter安装情况"]
        }
        
        for failed_check in failed_checks:
            if failed_check in suggestions:
                self.log(f"\n  {failed_check}:")
                for suggestion in suggestions[failed_check]:
                    self.log(f"    {suggestion}")
    
    def get_available_check_options(self):
        """获取所有可用的检查选项"""
        return [
            "Python环境",
            "必需模块",
            "可选模块",
            "项目模块",
            "目录结构",
            "模板文件",
            "数据文件夹",
            "公司材料包",
            "ZIP解压功能",
            "文件夹清理功能",
            "文件夹提取功能",
            "Word转PDF功能",
            "文件重命名功能",
            "GUI功能"
        ]
    
    def run_comprehensive_check(self):
        """运行综合检查"""
        self.log("开始综合功能检查...")
        self.log("=" * 60)
        
        # 执行各项检查
        checks = [
            ("Python环境", self.check_python_environment),
            ("必需模块", self.check_required_modules),
            ("可选模块", self.check_optional_modules),
            ("项目模块", self.check_project_modules),
            ("目录结构", self.check_directory_structure),
            ("模板文件", self.check_template_files),
            ("数据文件夹", self.check_data_folder_samples),
            ("公司材料包", self.check_company_package_structure),
            ("ZIP解压功能", self.check_function_zip_extraction),
            ("文件夹清理功能", self.check_function_folder_cleaning),
            ("文件夹提取功能", self.check_function_folder_extraction),
            ("Word转PDF功能", self.check_function_word_to_pdf),
            ("文件重命名功能", self.check_function_file_renaming),
            ("GUI功能", self.check_gui_functionality)
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_func in checks:
            self.log(f"\n=== 检查 {check_name} ===")
            try:
                result = check_func()
                self.check_results[check_name] = result
                if result:
                    passed_checks += 1
            except Exception as e:
                self.log(f"{check_name} 检查失败: {e}")
                self.check_results[check_name] = False
        
        # 显示总结
        self.log("\n" + "=" * 60)
        self.log("功能检查总结:")
        self.log(f"  通过检查: {passed_checks}/{total_checks}")
        self.log(f"  未通过检查: {total_checks - passed_checks}/{total_checks}")
        self.log(f"  📈 检查通过率: {(passed_checks / total_checks * 100):.1f}%")
        
        # 显示具体结果
        self.log("\n详细结果:")
        for check_name, result in self.check_results.items():
            status = "通过" if result else "失败"
            self.log(f"  {status} {check_name}")
        
        # 给出建议
        if passed_checks == total_checks:
            self.log("\n所有功能检查通过！程序可以正常使用。")
            self.log("建议:")
            self.log("  • 可以开始使用所有功能")
            self.log("  • 如需要Word转PDF功能，请确保安装了Microsoft Word")
            self.log("  • 定期运行功能检查以确保环境正常")
        else:
            self.log("\n 部分功能检查未通过，请解决以下问题:")
            
            failed_checks = [name for name, result in self.check_results.items() if not result]
            for failed_check in failed_checks:
                self.log(f"  • {failed_check}")
            
            self.log("\n解决建议:")
            if not self.check_results.get("必需模块", True):
                self.log("  • 安装缺失的Python包: pip install <包名>")
            if not self.check_results.get("目录结构", True):
                self.log("  • 创建缺失的必需目录")
            if not self.check_results.get("模板文件", True):
                self.log("  • 检查模板文件格式是否正确")
            if not self.check_results.get("公司材料包", True):
                self.log("  • 检查data文件夹下是否存在公司材料包")
                self.log("  • 确保材料包文件夹格式正确（编号_公司名称_材料包）")
            if not self.check_results.get("Word转PDF功能", True):
                self.log("  • 安装pywin32: pip install pywin32")
                self.log("  • 确保安装了Microsoft Word")
        
        return passed_checks == total_checks

    def _get_folder_patterns(self, template_name=None):
        """获取文件夹匹配模式"""
        if template_name:
            # 从指定模板获取模式
            template_path = get_resource_path(f"template/data_read_templates/{template_name}.json")
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
                    self.log(f"   读取模板失败 {template_name}: {e}")

        # 默认模式
        return ["*材料包", "*_*_*"]

    def _match_folder_patterns(self, folder_name, patterns):
        """检查文件夹名是否匹配任一模式"""
        import fnmatch
        for pattern in patterns:
            if fnmatch.fnmatch(folder_name, pattern):
                return True
        return False

def run_function_check_standalone():
    """独立运行功能检查"""
    checker = FunctionChecker()
    return checker.run_comprehensive_check()

if __name__ == "__main__":
    try:
        success = run_function_check_standalone()
        
        print(f"\n{'='*60}")
        if success:
            print("功能检查完成，所有功能正常！")
        else:
            print("功能检查发现问题，请查看上方详细信息。")
        
        input("\n按回车键退出...")
        
    except KeyboardInterrupt:
        print("\n 检查被用户中断")
    except Exception as e:
        print(f"\n检查过程中发生错误: {e}")
        traceback.print_exc()
        input("\n按回车键退出...")