#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业材料文档处理工具 - 主程序
集成了ZIP解压、文件夹清理、文件夹提取、Word转PDF、文件重命名等功能

新增功能：
- 规则管理中心：统一管理所有规则模板（重命名、文件夹提取、Word转PDF、清理规则）

依赖模块：
- 标准库: tkinter, threading, queue, sys, os, subprocess, json, fnmatch, pathlib, traceback
- 项目模块:
  * template_validator.py - 模板验证器
  * cache_manager.py - 缓存管理器
  * analyze_zip_encoding.py - ZIP文件解压和编码处理
  * clean_folder.py - 文件夹清理功能
  * extract_folders.py - 文件夹提取功能
  * final_word_to_pdf.py - Word转PDF转换功能
  * universal_rename.py - 文件重命名功能
  * pdf_merger.py - PDF合并功能
  * function_checker.py - 功能检查器
  * environmenst_test.py - 环境测试功能

作者：Lxx   更新时间：2025-10-13
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import sys
import os
import subprocess
import json
import fnmatch
from pathlib import Path
import traceback

# 导入模板验证器
try:
    from template_validator import validate_template_content
except ImportError:
    print("警告：无法导入模板验证器，将使用基础验证功能")
    # 创建一个基础的验证函数作为后备
    def validate_template_content(content, template_type=None):
        """基础模板验证函数（后备方案）"""
        try:
            if isinstance(content, str):
                json.loads(content)
            return True, []
        except json.JSONDecodeError as e:
            return False, [f"JSON格式错误: {e}"]

# 获取资源文件的正确路径（支持打包后的exe）
def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和打包后的exe环境"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下使用当前工作目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 导入缓存管理器
try:
    from cache_manager import GUICacheManager
except ImportError as e:
    print(f"无法导入缓存管理器: {e}")
    print("请确保cache_manager.py文件存在")
    # 创建一个简单的替代类以防导入失败
    class GUICacheManager:
        def __init__(self, cache_file="gui_cache.json"):
            self.cache_dir = ".cache"
            self.cache_file = os.path.join(self.cache_dir, cache_file)
            self._ensure_cache_directory()
            self.default_cache = {
                "window": {"width": 1280, "height": 960, "x": None, "y": None},
                "templates": {"selected_rename_template": None, "selected_extract_template": None,
                             "selected_word_template": None, "selected_clean_template": None},
                "paths": {"current_package_path": None},
                "ui_state": {"last_used_templates": []}
            }

        def _ensure_cache_directory(self):
            """确保缓存目录存在"""
            try:
                if not os.path.exists(self.cache_dir):
                    os.makedirs(self.cache_dir, exist_ok=True)
            except Exception as e:
                print(f"创建缓存目录失败: {e}")

        def load_cache(self):
            return self.default_cache.copy()

        def save_cache(self, data):
            """保存缓存数据到文件"""
            try:
                if json is None:
                    print("警告：无法保存缓存，json模块不可用")
                    return

                # 确保目录存在
                os.makedirs(os.path.dirname(self.cache_file) if os.path.dirname(self.cache_file) else '.', exist_ok=True)
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存缓存失败: {e}")

        def load_cache(self):
            """加载缓存数据"""
            try:
                if json is None:
                    print("警告：无法加载缓存，json模块不可用")
                    return self.default_cache.copy()

                if os.path.exists(self.cache_file):
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    return self.default_cache.copy()
            except Exception as e:
                print(f"加载缓存失败: {e}")
                return self.default_cache.copy()

        def save_cache_data(self, root, templates=None, paths=None, ui_state=None):
            """保存完整的缓存数据"""
            try:
                if json is None:
                    print("警告：无法保存缓存数据，json模块不可用")
                    return

                # 加载现有缓存
                cache_data = self.load_cache()

                # 更新模板信息
                if templates:
                    templates_cache = cache_data.setdefault("templates", {})
                    templates_cache.update(templates)

                # 更新路径信息
                if paths:
                    paths_cache = cache_data.setdefault("paths", {})
                    paths_cache.update(paths)

                # 更新UI状态信息
                if ui_state:
                    cache_data.setdefault("ui_state", {}).update(ui_state)

                # 保存到文件
                self.save_cache(cache_data)

            except Exception as e:
                print(f"保存缓存数据失败: {e}")

        def get_window_geometry(self, root):
            return {"width": 1280, "height": 960, "x": None, "y": None}

        def set_window_geometry(self, root, geometry):
            root.geometry("1280x960")

# 导入各个功能模块
try:
    from analyze_zip_encoding import unzip_files_in_data_folder
    from clean_folder import process_data_folders
    from extract_folders import scan_material_packages, FolderExtractor
    from final_word_to_pdf import batch_convert_data_folder
    from universal_rename import scan_data_folder, batch_process_all_data
    from pdf_merger import PDFProcessor
    from function_checker import FunctionChecker
    from environmenst_test import run_full_test

except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖文件都在同一目录下")
    sys.exit(1)

class MedicalDocProcessor:
    def __init__(self):
        # 初始化缓存管理器
        self.cache_manager = GUICacheManager()

        # 加载缓存数据
        self.cache_data = self.cache_manager.load_cache()

        self.root = tk.Tk()
        self.root.title("企业材料文档处理工具 v1.0")

        # 从缓存中恢复窗口大小和位置
        self.cache_manager.set_window_geometry(self.root, self.cache_data.get("window", {}))

        self.root.resizable(True, True)

        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 创建消息队列用于线程间通信
        self.message_queue = queue.Queue()

        # 当前工作线程
        self.current_thread = None

        # 后台任务状态标志
        self.word_to_pdf_running = False
        self.rename_running = False
        self.clean_running = False
        self.extract_running = False
        self.unzip_running = False

        # 从缓存中恢复模板选择
        templates_cache = self.cache_data.get("templates", {})
        self.selected_rename_template = templates_cache.get("selected_rename_template")
        self.selected_extract_template = templates_cache.get("selected_extract_template")
        self.selected_word_template = templates_cache.get("selected_word_template")
        self.selected_clean_template = templates_cache.get("selected_clean_template")
        self.selected_material_package_template = templates_cache.get("selected_material_package_template")

        # 调试信息：打印加载的模板设置（可选）
        # print(f"[启动] 加载的模板设置:")
        # print(f"  重命名模板: {self.selected_rename_template}")
        # print(f"  提取模板: {self.selected_extract_template}")
        # print(f"  Word转PDF模板: {self.selected_word_template}")
        # print(f"  清理模板: {self.selected_clean_template}")
        # print(f"  材料包查找模板: {self.selected_material_package_template}")

        # 当前选择的公司材料包路径
        self.current_package_path = self.cache_data.get("paths", {}).get("current_package_path")
        
        # 规则数据缓存（用于自动化流程）
        self.all_rules = {
            "重命名规则": {},
            "文件夹提取规则": {},
            "Word转PDF规则": {},
            "清理规则": {},
            "材料包查找规则": {}
        }
        
        # 加载规则
        self.load_all_rules()
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息处理
        self.process_messages()

    def on_closing(self):
        """窗口关闭时的处理"""
        # 检查是否有后台任务在运行
        if self.current_thread and self.current_thread.is_alive():
            # 显示等待对话框
            self.log_message("检测到后台任务正在运行...")
            self.log_message("请等待任务完成后再关闭程序")

            # 弹出确认对话框
            response = messagebox.askyesno(
                "后台任务进行中",
                "有后台任务正在运行中。\n\n"
                "请等待任务完成后再关闭程序，或者确认要强制关闭？\n\n"
                "注意：强制关闭可能导致任务失败或数据丢失。",
                icon='warning'
            )

            if not response:
                # 用户选择等待，不关闭程序
                return
            else:
                # 用户选择强制关闭，记录警告日志
                self.log_message("用户选择强制关闭程序，后台任务可能被中断")

        # 保存缓存数据
        self.save_cache_data()
        self.root.destroy()

    def save_cache_data(self):
        """保存缓存数据"""
        try:
            # 准备模板数据
            templates = {
                "selected_rename_template": self.selected_rename_template,
                "selected_extract_template": self.selected_extract_template,
                "selected_word_template": self.selected_word_template,
                "selected_clean_template": self.selected_clean_template,
                "selected_material_package_template": self.selected_material_package_template
            }

            # 准备路径数据
            paths = {
                "current_package_path": self.current_package_path
            }

            # 保存缓存数据
            self.cache_manager.save_cache_data(
                root=self.root,
                templates=templates,
                paths=paths
            )

        except Exception as e:
            print(f"保存缓存数据失败: {e}")

    def create_widgets(self):
        """创建主界面组件"""
        
        # 主标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, text="企业材料文档处理工具",
                               font=('Microsoft YaHei', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="自动化处理企业材料申报材料",
                                  font=('Microsoft YaHei', 10))
        subtitle_label.pack()
        
        # 创建主要功能区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左侧功能按钮区域
        left_frame = ttk.LabelFrame(main_frame, text="⚙️ 功能选择", padding=10)
        left_frame.pack(side='left', fill='y', padx=(0, 5))
        
        # 右侧日志显示区域
        right_frame = ttk.LabelFrame(main_frame, text="操作日志", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # 功能按钮
        self.create_function_buttons(left_frame)
        
        # 日志显示区域
        self.create_log_area(right_frame)
        
        # 底部状态栏
        self.create_status_bar()
    
    def load_all_rules(self):
        """加载所有规则模板"""
        try:
            from pathlib import Path
            
            # 加载重命名规则
            rename_dir = Path(get_resource_path("template/rename_templates"))
            if rename_dir.exists():
                for json_file in rename_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            rule_data = json.load(f)
                        self.all_rules["重命名规则"][json_file.stem] = rule_data
                    except:
                        pass
            
            # 加载文件夹提取规则
            folder_dir = Path(get_resource_path("template/folder_templates"))
            if folder_dir.exists():
                for json_file in folder_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            rule_data = json.load(f)
                        self.all_rules["文件夹提取规则"][json_file.stem] = rule_data
                    except:
                        pass
            
            # 加载Word转PDF规则
            word_dir = Path(get_resource_path("template/word_to_pdf_templates"))
            if word_dir.exists():
                for json_file in word_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            rule_data = json.load(f)
                        self.all_rules["Word转PDF规则"][json_file.stem] = rule_data
                    except:
                        pass
            
            # 加载清理规则
            clean_dir = Path(get_resource_path("template/clean_templates"))
            if clean_dir.exists():
                for json_file in clean_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            rule_data = json.load(f)
                        self.all_rules["清理规则"][json_file.stem] = rule_data
                    except:
                        pass
            
            # 加载材料包查找规则
            material_dir = Path(get_resource_path("template/data_read_templates"))
            if material_dir.exists():
                for json_file in material_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            rule_data = json.load(f)
                        self.all_rules["材料包查找规则"][json_file.stem] = rule_data
                    except:
                        pass
        except Exception as e:
            print(f"加载规则失败: {e}")
    
    def create_function_buttons(self, parent):
        """创建功能按钮"""
        
        # 自动化流程区域
        auto_frame = ttk.LabelFrame(parent, text="自动化流程", padding=5)
        auto_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(auto_frame, text="完整自动化流程", 
                  command=self.run_full_automation, 
                  width=20).pack(pady=2)
        
        ttk.Button(auto_frame, text="自定义流程", 
                  command=self.run_custom_automation, 
                  width=20).pack(pady=2)
        
        # 分隔线
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # 单独功能区域
        single_frame = ttk.LabelFrame(parent, text="单独功能", padding=5)
        single_frame.pack(fill='x')
        
        # 各个功能按钮
        functions = [
            ("解压ZIP文件", self.run_unzip),
            ("清理文件夹", self.run_clean),
            ("Word转PDF", self.run_word_to_pdf),
            ("文件重命名", self.run_rename),
            ("提取文件夹", self.run_extract),
            ("合并PDF文件", self.run_pdf_merge),
        ]
        
        for text, command in functions:
            ttk.Button(single_frame, text=text, command=command, width=20).pack(pady=2)
        
        # 分隔线
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # 工具按钮区域
        tools_frame = ttk.LabelFrame(parent, text="实用工具", padding=5)
        tools_frame.pack(fill='x')
        
        ttk.Button(tools_frame, text="功能检查 ▼",
                  command=self.show_check_menu, width=20).pack(pady=2)
        ttk.Button(tools_frame, text="检查材料包",
                  command=self.check_company_package, width=20).pack(pady=2)
        ttk.Button(tools_frame, text="清空日志",
                  command=self.clear_log, width=20).pack(pady=2)
        ttk.Button(tools_frame, text="保存日志",
                  command=self.save_log, width=20).pack(pady=2)
        #  创建设置管理按钮和菜单
        # settings_frame = ttk.Frame(tools_frame)
        # settings_frame.pack(fill='x', pady=2)

        # settings_btn = ttk.Button(settings_frame, text="设置管理 ▼",
        #                          command=self.show_settings_menu, width=20)
        # settings_btn.pack()

        # # 创建右键菜单
        # self.settings_menu = tk.Menu(settings_btn, tearoff=0)
        # self.settings_menu.add_command(label="导出设置", command=self.export_cache_settings)
        # self.settings_menu.add_command(label="导入设置", command=self.import_cache_settings)

        ttk.Button(tools_frame, text="规则管理 ▼",
                  command=self.show_rule_manager, width=20).pack(pady=2)

    def show_settings_menu(self):
        """显示设置管理菜单"""
        try:
            # 在鼠标位置显示菜单
            self.settings_menu.tk_popup(
                self.root.winfo_pointerx(),
                self.root.winfo_pointery()
            )
        finally:
            self.settings_menu.grab_release()

    def create_log_area(self, parent):
        """创建日志显示区域"""
        self.log_text = scrolledtext.ScrolledText(parent, 
                                                 wrap=tk.WORD, 
                                                 height=25, 
                                                 font=('Consolas', 11))
        self.log_text.pack(fill='both', expand=True)
        
        # 添加欢迎信息
        welcome_msg = """欢迎使用企业材料文档预处理工具！

功能介绍：
- 解压ZIP文件：自动解压data文件夹中的所有ZIP文件，正确处理中文编码
- 清理文件夹：清理文件夹，只保留材料包文件夹
- 提取文件夹：根据模板提取指定文件夹到output目录
- Word转PDF：批量转换Word文件为PDF格式
- 文件重命名：根据模板为文件添加标识标签
- PDF合并：打开PDF合并管理器，选择文件、设置顺序进行合并

自动化流程：
- 完整流程：依次执行所有功能步骤
- 自定义流程：选择需要的功能步骤

使用提示：
1. 请确保data文件夹位于程序同目录下
2. 建议先备份重要文件
3. 操作过程中请勿关闭程序

准备就绪，请选择功能开始处理！
"""
        self.log_text.insert(tk.END, welcome_msg)
        self.log_text.see(tk.END)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill='x', side='bottom')
        
        self.status_label = ttk.Label(self.status_frame, text="就绪", relief='sunken')
        self.status_label.pack(side='left', fill='x', expand=True)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side='right', padx=5)
    
    def log_message(self, message):
        """添加日志消息"""
        self.message_queue.put(('log', message))
    
    def set_status(self, status):
        """设置状态栏文本"""
        self.message_queue.put(('status', status))
    
    def start_progress(self):
        """开始进度条动画"""
        self.message_queue.put(('progress', 'start'))
    
    def stop_progress(self):
        """停止进度条动画"""
        self.message_queue.put(('progress', 'stop'))

    def check_company_package(self):
        """检查公司材料包结构"""
        self.log_message("开始检查公司材料包结构...")

        try:
            # 导入功能检查器
            from function_checker import FunctionChecker

            # 创建检查器实例，传入日志回调函数
            checker = FunctionChecker(log_callback=self.log_message)

            # 获取用户选择的材料包查找规则
            selected_template = self.selected_material_package_template
            if selected_template:
                self.log_message(f"使用材料包查找规则: {selected_template}")
                # 运行公司材料包结构检查，使用用户选择的规则
                result = checker.check_company_package_structure(selected_template)
            else:
                self.log_message("使用默认规则检查材料包结构")
                # 运行公司材料包结构检查，使用默认规则
                result = checker.check_company_package_structure()

            if result:
                self.log_message("公司材料包结构检查完成，所有材料包结构正常。")
            else:
                self.log_message("公司材料包结构检查发现问题，请查看上方详细信息。")

        except ImportError as e:
            self.log_message(f"无法导入功能检查器: {e}")
            self.log_message("请检查function_checker.py文件是否存在")

        except Exception as e:
            self.log_message(f"公司材料包检查失败: {e}")
            import traceback
            self.log_message(f"详细错误: {traceback.format_exc()}")

    def select_company_package(self, use_template_rules=None, template_name=None):
        """选择公司材料包目录

        Args:
            use_template_rules: 是否使用模板规则进行匹配，如果为None则自动判断
            template_name: 模板名称，如果为None则使用用户选择的模板
        """
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
            messagebox.showerror("错误", "未找到data文件夹！\n请确保项目根目录下有data文件夹。")
            return None

        # 自动判断是否使用模板规则
        if use_template_rules is None:
            use_template_rules = bool(self.selected_material_package_template)

        # 如果没有指定模板名称，使用用户选择的模板
        if use_template_rules and not template_name:
            template_name = self.selected_material_package_template

        # 获取文件夹匹配模式
        folder_patterns = self._get_folder_patterns(use_template_rules, template_name)

        # 扫描所有公司材料包目录
        package_dirs = []
        try:
            # 先扫描一级目录
            for item in data_path.iterdir():
                if item.is_dir():
                    dir_name = item.name
                    # 根据规则匹配文件夹
                    if self._match_folder_patterns(dir_name, folder_patterns):
                        package_dirs.append((dir_name, str(item)))

            # 如果一级目录没找到，再扫描二级目录
            if not package_dirs:
                for item in data_path.iterdir():
                    if item.is_dir():
                        # 在每个子目录中查找材料包
                        for sub_item in item.iterdir():
                            if sub_item.is_dir():
                                sub_dir_name = sub_item.name
                                if self._match_folder_patterns(sub_dir_name, folder_patterns):
                                    package_dirs.append((sub_dir_name, str(sub_item)))

        except Exception as e:
            messagebox.showerror("错误", f"扫描data文件夹时出错：{str(e)}")
            return None

        if not package_dirs:
            # 提供更详细的错误信息
            error_msg = "未找到任何公司材料包！\n\n请确保data文件夹下有格式为'编号_公司名称_材料包'的目录。\n\n"
            error_msg += f"当前检查的路径：{data_path.absolute()}\n"
            error_msg += "找到的文件夹：\n"

            try:
                all_dirs = [item.name for item in data_path.iterdir() if item.is_dir()]
                if all_dirs:
                    for dir_name in all_dirs[:10]:  # 只显示前10个
                        error_msg += f"  • {dir_name}\n"
                    if len(all_dirs) > 10:
                        error_msg += f"  ... 还有 {len(all_dirs) - 10} 个文件夹\n"
                else:
                    error_msg += "  无文件夹\n"
            except:
                error_msg += "  无法读取文件夹内容\n"

            messagebox.showerror("错误", error_msg)
            return None

        # 创建选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择公司材料包")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # 创建列表框
        listbox = tk.Listbox(dialog, width=60, height=15)
        listbox.pack(padx=10, pady=10, fill='both', expand=True)

        # 添加选项
        for dir_name, dir_path in package_dirs:
            listbox.insert(tk.END, f"{dir_name} ({dir_path})")

        def on_select():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                selected_name, selected_path = package_dirs[index]
                self.current_package_path = selected_path
                self.log_message(f"已选择公司材料包: {selected_name}")

                # 保存到缓存
                self.save_cache_data()

                dialog.destroy()
            else:
                messagebox.showwarning("警告", "请选择一个公司材料包！")

        # 按钮框架
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(padx=10, pady=5, fill='x')

        ttk.Button(btn_frame, text="选择", command=on_select).pack(side='right', padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='right')

        # 等待用户选择
        self.root.wait_window(dialog)

        return self.current_package_path

    def _get_folder_patterns(self, use_template_rules=False, template_name=None):
        """获取文件夹匹配模式"""
        if use_template_rules and template_name:
            # 从指定模板获取模式（使用get_resource_path支持打包后的exe）
            template_path = get_resource_path(f"template/data_read_templates/{template_name}.json")
            if os.path.exists(template_path):
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    patterns = []
                    rules = template_data.get('rules', [])
                    for rule in rules:
                        if rule.get('type') == 'folder':
                            pattern = rule.get('pattern', '')
                            if pattern:
                                patterns.append(pattern)
                    if patterns:
                        return patterns
                except:
                    pass

        # 默认模式
        return ["*材料包"]

    def _match_folder_patterns(self, folder_name, patterns):
        """检查文件夹名是否匹配任一模式"""
        for pattern in patterns:
            if fnmatch.fnmatch(folder_name, pattern):
                return True
        return False

    def process_messages(self):
        """处理消息队列中的消息"""
        try:
            while True:
                msg_type, content = self.message_queue.get_nowait()

                if msg_type == 'log':
                    self.log_text.insert(tk.END, f"{content}\n")
                    self.log_text.see(tk.END)
                elif msg_type == 'status':
                    self.status_label.config(text=content)
                elif msg_type == 'progress':
                    if content == 'start':
                        self.progress.start()
                    else:
                        self.progress.stop()

        except queue.Empty:
            pass

        # 每100ms检查一次消息队列
        self.root.after(100, self.process_messages)
    
    def run_in_thread(self, func, *args, **kwargs):
        """在新线程中运行函数"""
        if self.current_thread and self.current_thread.is_alive():
            messagebox.showwarning("警告", "已有任务正在运行，请等待完成！")
            return
        
        self.current_thread = threading.Thread(target=self._thread_wrapper, 
                                             args=(func,) + args, 
                                             kwargs=kwargs)
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def _thread_wrapper(self, func, *args, **kwargs):
        """线程包装器，用于异常处理"""
        try:
            self.start_progress()
            func(*args, **kwargs)
        except Exception as e:
            error_msg = f"执行过程中发生错误：{str(e)}"
            self.log_message(error_msg)
            traceback.print_exc()
        finally:
            self.stop_progress()
            self.set_status("就绪")
    
    # 各个功能的实现方法
    def run_unzip(self):
        """运行ZIP解压功能"""
        self.run_in_thread(self._unzip_worker)
    
    def _unzip_worker(self):
        self.unzip_running = True  # 设置解压状态为运行中
        self.set_status("正在解压ZIP文件...")
        self.log_message("开始解压ZIP文件...")

        # 重定向输出到日志
        original_print = print
        def log_print(*args, **kwargs):
            message = ' '.join(str(arg) for arg in args)
            self.log_message(message)

        import builtins
        builtins.print = log_print

        try:
            unzip_files_in_data_folder()
            self.log_message("ZIP解压完成！")
        finally:
            self.unzip_running = False  # 清除解压状态标志
            builtins.print = original_print
    
    def run_clean(self):
        """运行文件夹清理功能"""
        self.run_in_thread(self._clean_worker)
    
    def _clean_worker(self):
        self.clean_running = True  # 设置清理状态为运行中
        self.set_status("正在清理文件夹...")
        self.log_message("开始清理文件夹...")

        # GUI模式的确认回调函数
        def confirmation_callback(title, message):
            return messagebox.askyesno(title, message)

        # 重定向输出到日志
        original_print = print
        def log_print(*args, **kwargs):
            message = ' '.join(str(arg) for arg in args)
            self.log_message(message)

        import builtins
        builtins.print = log_print

        try:
            process_data_folders(gui_mode=True, confirmation_callback=confirmation_callback)
            self.log_message("文件夹清理完成！")
        finally:
            self.clean_running = False  # 清除清理状态标志
            builtins.print = original_print
    
    def run_extract(self):
        """运行文件夹提取功能（使用选择的模板）"""
        # 检查是否已选择提取模板
        if not self.selected_extract_template:
            self.log_message("请先在规则管理中选择提取模板")
            # 打开规则管理对话框让用户选择
            rule_dialog = RuleManagerDialog(self.root, self.log_message)
            self.root.wait_window(rule_dialog.dialog)
            return

        self.run_in_thread(self._extract_worker, self.selected_extract_template)
    
    def _extract_worker(self, selected_template):
        self.extract_running = True  # 设置提取状态为运行中
        self.set_status("正在提取文件夹...")
        self.log_message("开始提取文件夹...")

        # 使用选择的模板
        self.log_message(f"使用模板: {selected_template}")

        # 扫描材料包（使用用户选择的材料包查找规则）
        selected_package_template = self.selected_material_package_template
        if selected_package_template:
            self.log_message(f"使用材料包查找规则: {selected_package_template}")
            material_packages = scan_material_packages(selected_package_template)
        else:
            self.log_message("使用默认规则扫描材料包")
            material_packages = scan_material_packages()
        if not material_packages:
            self.log_message("没有找到材料包文件夹")
            return
        
        self.log_message(f"找到 {len(material_packages)} 个材料包")
        
        # 批量处理
        extractor = FolderExtractor(selected_template)
        
        # 清空output文件夹
        if os.path.exists(extractor.output_folder):
            import shutil
            shutil.rmtree(extractor.output_folder)
            self.log_message("已清空输出文件夹")
        
        success_count = 0
        for i, package in enumerate(material_packages, 1):
            package_name = os.path.basename(package)
            self.log_message(f"[{i}/{len(material_packages)}] 处理: {package_name}")
            
            # 重定向输出
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.log_message(message)
            
            import builtins
            builtins.print = log_print
            
            try:
                if extractor.extract_folders(package):
                    success_count += 1
            finally:
                builtins.print = original_print
        
        self.log_message(f"文件夹提取完成！成功处理 {success_count}/{len(material_packages)} 个材料包")
        self.extract_running = False  # 清除提取状态标志
    
    def run_word_to_pdf(self):
        """运行Word转PDF功能"""
        self.run_in_thread(self._word_to_pdf_worker)
    
    def _word_to_pdf_worker(self):
        self.word_to_pdf_running = True  # 设置转换状态为运行中
        self.set_status("正在转换Word文件...")
        self.log_message("开始Word转PDF转换（使用WPS）...")

        # GUI模式的确认回调函数
        def confirmation_callback(title, message):
            return messagebox.askyesno(title, message)

        # 重定向输出到日志
        original_print = print
        def log_print(*args, **kwargs):
            message = ' '.join(str(arg) for arg in args)
            self.log_message(message)

        import builtins
        builtins.print = log_print

        try:
            # 获取选择的Word转PDF模板路径
            template_path = None
            
            # 添加调试信息
            self.log_message(f"检查Word转PDF模板选择...")
            self.log_message(f"hasattr(self, 'selected_word_template'): {hasattr(self, 'selected_word_template')}")
            if hasattr(self, 'selected_word_template'):
                self.log_message(f"self.selected_word_template = {self.selected_word_template}")
            
            if hasattr(self, 'selected_word_template') and self.selected_word_template:
                # 从模板键名构建完整路径（使用get_resource_path支持打包后的exe）
                template_name = self.selected_word_template
                relative_path = f"template/word_to_pdf_templates/{template_name}.json"
                template_path = get_resource_path(relative_path)
                self.log_message(f"使用Word转PDF规则: {template_name}")
                self.log_message(f"模板文件路径: {template_path}")
                self.log_message(f"模板文件是否存在: {os.path.exists(template_path)}")
            else:
                self.log_message("未选择Word转PDF规则，将处理所有Word文件")

            # 执行WPS转换
            self.log_message("正在启动WPS Office...")
            result = batch_convert_data_folder(gui_mode=True, confirmation_callback=confirmation_callback, template_path=template_path)
            if result:
                self.log_message("Word转PDF完成！")
            else:
                self.log_message("Word转PDF过程中出现问题")
        except Exception as e:
            self.log_message(f"Word转PDF异常: {str(e)}")
            import traceback
            self.log_message(f"错误堆栈: {traceback.format_exc()}")
        finally:
            self.word_to_pdf_running = False  # 清除转换状态标志
            builtins.print = original_print
    
    def run_rename(self):
        """运行文件重命名功能（使用选择的模板）"""
        # 检查是否已选择重命名模板
        if not self.selected_rename_template:
            self.log_message("请先在规则管理中选择重命名模板")
            # 打开规则管理对话框让用户选择
            rule_dialog = RuleManagerDialog(self.root, self.log_message)
            self.root.wait_window(rule_dialog.dialog)
            return

        self.run_in_thread(self._rename_worker, self.selected_rename_template)
    
    def run_pdf_merge(self):
        """运行PDF合并功能"""
        # 创建PDF合并管理窗口
        pdf_merge_dialog = PDFMergeDialog(self.root, self, self.log_message)
        self.root.wait_window(pdf_merge_dialog.dialog)

    def _rename_worker(self, selected_template):
        self.rename_running = True  # 设置重命名状态为运行中
        self.set_status("正在重命名文件...")
        self.log_message("开始文件重命名...")

        # 使用选择的模板
        self.log_message(f"使用重命名模板: {selected_template}")

        # GUI模式的确认回调函数
        def confirmation_callback(title, message):
            return messagebox.askyesno(title, message)

        # 重定向输出到日志
        original_print = print
        def log_print(*args, **kwargs):
            message = ' '.join(str(arg) for arg in args)
            self.log_message(message)

        import builtins
        builtins.print = log_print

        try:
            # 获取用户选择的材料包查找规则
            selected_package_template = self.selected_material_package_template
            result = batch_process_all_data(selected_template, gui_mode=True, confirmation_callback=confirmation_callback, material_package_template=selected_package_template)
            if result:
                self.log_message("文件重命名完成！")
            else:
                self.log_message("文件重命名过程中出现问题")
        finally:
            self.rename_running = False  # 清除重命名状态标志
            builtins.print = original_print
    

    def run_full_automation(self):
        """运行完整自动化流程"""
        if self.current_thread and self.current_thread.is_alive():
            messagebox.showwarning("警告", "已有任务正在运行，请等待完成！")
            return
        
        # 确认对话框
        result = messagebox.askyesno("确认", 
                                   "即将执行完整自动化流程：\n\n" +
                                   "1. 解压ZIP文件\n" +
                                   "2. 清理文件夹\n" +
                                   "3. Word转PDF\n" +
                                   "4. 文件重命名\n" +
                                   "5. 提取文件夹\n\n" +
                                   "是否继续？")
        if not result:
            return
        
        self.run_in_thread(self._full_automation_worker)
    
    def _full_automation_worker(self):
        """完整自动化流程工作线程"""
        self.set_status("执行自动化流程...")
        self.log_message("开始完整自动化流程...")
        
        # 为自动化流程获取默认模板（如果没有选择，则使用第一个可用模板）
        rename_rules = self.all_rules.get("重命名规则", {})
        default_rename_template = next(iter(rename_rules.keys())) if rename_rules else None

        extract_rules = self.all_rules.get("文件夹提取规则", {})
        default_extract_template = next(iter(extract_rules.keys())) if extract_rules else None
        
        steps = [
            ("解压ZIP文件", lambda: self._unzip_worker()),
            ("清理文件夹", lambda: self._clean_worker()),
            ("Word转PDF", lambda: self._word_to_pdf_worker()),
            ("文件重命名", lambda: self._rename_worker(default_rename_template)),
            ("提取文件夹", lambda: self._extract_worker(default_extract_template)),
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            self.log_message(f"\n{'='*50}")
            self.log_message(f"步骤 {i}/5: {step_name}")
            self.log_message(f"{'='*50}")

            try:
                step_func()
                self.log_message(f"{step_name} 完成")
            except Exception as e:
                self.log_message(f"{step_name} 失败: {e}")
                # 检查是否是关键步骤失败
                critical_steps = ["解压ZIP文件", "清理文件夹"]
                if step_name in critical_steps:
                    self.log_message(f"关键步骤失败，流程可能无法正常继续")
                    # 询问用户是否继续
                    if messagebox.askyesno("警告", f"步骤 '{step_name}' 失败，这是一个关键步骤。\n是否继续执行后续步骤？"):
                        continue
                    else:
                        self.log_message("用户选择停止流程执行")
                        break
                else:
                    # 非关键步骤失败，继续执行
                    continue
        
        self.log_message(f"\n完整自动化流程执行完成！")
    
    def run_custom_automation(self):
        """运行自定义自动化流程"""
        if self.current_thread and self.current_thread.is_alive():
            messagebox.showwarning("警告", "已有任务正在运行，请等待完成！")
            return

        # 创建选择对话框
        dialog = CustomFlowDialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.selected_steps:
            self.run_in_thread(self._custom_automation_worker, dialog.selected_steps)
    
    def _custom_automation_worker(self, selected_steps):
        """自定义自动化流程工作线程"""
        self.set_status("执行自定义流程...")
        self.log_message("开始自定义自动化流程...")
        
        # 为自定义流程获取默认模板（如果没有选择，则使用第一个可用模板）
        rename_rules = self.all_rules.get("重命名规则", {})
        default_rename_template = next(iter(rename_rules.keys())) if rename_rules else None

        extract_rules = self.all_rules.get("文件夹提取规则", {})
        default_extract_template = next(iter(extract_rules.keys())) if extract_rules else None
        
        step_functions = {
            "解压ZIP文件": lambda: self._unzip_worker(),
            "清理文件夹": lambda: self._clean_worker(),
            "Word转PDF": lambda: self._word_to_pdf_worker(),
            "文件重命名": lambda: self._rename_worker(default_rename_template),
            "提取文件夹": lambda: self._extract_worker(default_extract_template),
        }
        
        for i, step_name in enumerate(selected_steps, 1):
            self.log_message(f"\n{'='*50}")
            self.log_message(f"步骤 {i}/{len(selected_steps)}: {step_name}")
            self.log_message(f"{'='*50}")

            try:
                if step_name in step_functions:
                    step_functions[step_name]()
                    self.log_message(f"{step_name} 完成")
                else:
                    self.log_message(f" 未知的步骤: {step_name}")
                    continue
            except Exception as e:
                self.log_message(f"{step_name} 失败: {e}")
                # 检查是否是关键步骤失败
                critical_steps = ["解压ZIP文件", "清理文件夹"]
                if step_name in critical_steps:
                    self.log_message(f"关键步骤失败，流程可能无法正常继续")
                    # 询问用户是否继续
                    if messagebox.askyesno("警告", f"步骤 '{step_name}' 失败，这是一个关键步骤。\n是否继续执行后续步骤？"):
                        continue
                    else:
                        self.log_message("用户选择停止流程执行")
                        break
                else:
                    # 非关键步骤失败，继续执行
                    continue
        
        self.log_message(f"\n自定义自动化流程执行完成！")
    
    
    def show_check_menu(self):
        """显示检查菜单"""
        # 创建检查选项菜单
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="选择性检查", command=self.run_selective_check)
        menu.add_command(label="完整检查", command=self.run_comprehensive_check)
        menu.add_separator()
        menu.add_command(label="检查说明", command=self.show_check_help)

        # 获取鼠标位置显示菜单
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def run_selective_check(self):
        """运行选择性检查"""
        # 创建选择对话框
        dialog = CheckSelectionDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.selected_checks:
            self.run_in_thread(self._selective_check_worker, dialog.selected_checks)
    
    def run_comprehensive_check(self):
        """运行完整检查（原有的功能检查）"""
        self.run_in_thread(self._function_check_worker)
    
    def _selective_check_worker(self, selected_checks):
        """选择性检查工作线程"""
        self.set_status("正在进行选择性检查...")
        self.log_message(f"开始选择性功能检查（{len(selected_checks)}个项目）...")
        
        try:
            # 导入功能检查器
            from function_checker import FunctionChecker
            
            # 创建检查器实例，传入日志回调函数
            checker = FunctionChecker(log_callback=self.log_message)
            
            # 运行选择性检查
            result = checker.run_selective_check(selected_checks)
            
            if result:
                self.log_message("\n选择性检查完成！选中的所有功能正常可用。")
                self.log_message("选中的功能可以放心使用。")
            else:
                self.log_message("\n 选择性检查发现问题，请查看上方详细信息。")
                self.log_message("建议解决问题后再使用相关功能。")
                
        except ImportError as e:
            self.log_message(f"无法导入功能检查器: {e}")
            self.log_message("请检查function_checker.py文件是否存在")
                
        except Exception as e:
            self.log_message(f"选择性检查失败: {e}")
            import traceback
            self.log_message(f"详细错误: {traceback.format_exc()}")
    
    def show_check_help(self):
        """显示检查功能帮助信息"""
        help_text = """功能检查说明
选择性检查：
- 可以自由选择要检查的功能模块
- 适合针对性检查某些特定功能
- 节省时间，只检查需要的项目
完整检查：
- 检查所有功能模块（13项）
- 全面验证系统环境和功能
- 适合初次使用或完整验证
检查项目包括：
Python环境、必需模块、可选模块、项目模块、
目录结构、模板文件、数据文件夹、
ZIP解压功能、文件夹清理功能、文件夹提取功能、
Word转PDF功能、文件重命名功能、GUI功能
使用建议：
- 初次使用时建议运行完整检查
- 日常使用可选择针对性检查
- 遇到问题时先运行检查排查"""
        
        messagebox.showinfo("功能检查说明", help_text)
    
    def run_function_check(self):
        """运行功能检查（保留旧的接口，默认调用完整检查）"""
        self.run_comprehensive_check()
    
    def _function_check_worker(self):
        """功能检查工作线程"""
        self.set_status("正在进行功能检查...")
        self.log_message("开始功能检查...")
        
        try:
            # 导入功能检查器
            from function_checker import FunctionChecker
            
            # 创建检查器实例，传入日志回调函数
            checker = FunctionChecker(log_callback=self.log_message)
            
            # 运行综合检查
            result = checker.run_comprehensive_check()
            
            if result:
                self.log_message("\n功能检查完成！所有功能正常可用。")
                self.log_message("您可以放心使用所有功能。")
            else:
                self.log_message("\n 功能检查发现问题，请查看上方详细信息。")
                self.log_message("建议解决问题后再使用相关功能。")
                
        except ImportError as e:
            self.log_message(f"无法导入功能检查器: {e}")
            self.log_message("使用基础环境检查...")
            
            # 退回到基础检查
            try:
                from environmenst_test import run_full_test
                
                # 重定向输出到日志
                original_print = print
                def log_print(*args, **kwargs):
                    message = ' '.join(str(arg) for arg in args)
                    self.log_message(message)
                
                import builtins
                builtins.print = log_print
                
                try:
                    result = run_full_test()
                    if result:
                        self.log_message("基础环境检查通过！")
                    else:
                        self.log_message(" 基础环境检查发现问题")
                finally:
                    builtins.print = original_print
                    
            except Exception as fallback_error:
                self.log_message(f"基础检查也失败了: {fallback_error}")
                
        except Exception as e:
            self.log_message(f"功能检查失败: {e}")
            import traceback
            self.log_message(f"详细错误: {traceback.format_exc()}")
    

    def show_rule_manager(self):
        """显示规则管理对话框"""
        # 创建规则管理对话框
        rule_dialog = RuleManagerDialog(self, self.log_message)
        self.root.wait_window(rule_dialog.dialog)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空")
    
    def save_log(self):
        """保存日志"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="保存日志文件"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"日志已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {e}")

    def export_cache_settings(self):
        """导出缓存设置到文件"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导出缓存设置"
        )
        if filename:
            try:
                # 准备导出数据（包含当前所有设置）
                export_data = {
                    "window": self.cache_manager.get_window_geometry(self.root),
                    "templates": {
                        "selected_rename_template": self.selected_rename_template,
                        "selected_extract_template": self.selected_extract_template,
                        "selected_word_template": self.selected_word_template,
                        "selected_clean_template": self.selected_clean_template
                    },
                    "paths": {
                        "current_package_path": self.current_package_path
                    },
                    "export_info": {
                        "export_time": "2024-10-15",  # 这里可以用实际时间
                        "version": "1.0.0",
                        "description": "企业材料文档预处理工具缓存设置"
                    }
                }

                # 保存到文件
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)

                self.log_message(f"缓存设置已导出到: {filename}")
                messagebox.showinfo("成功", f"缓存设置已导出到:\n{filename}")

            except Exception as e:
                error_msg = f"导出缓存设置失败: {e}"
                self.log_message(error_msg)
                messagebox.showerror("错误", error_msg)

    def import_cache_settings(self):
        """从文件导入缓存设置"""
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导入缓存设置"
        )
        if filename:
            try:
                # 读取文件
                with open(filename, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)

                # 验证文件格式
                if not isinstance(import_data, dict):
                    raise ValueError("文件格式不正确")

                # 询问用户是否要应用这些设置
                templates_info = import_data.get("templates", {})
                window_info = import_data.get("window", {})

                confirm_msg = "即将导入以下设置：\n\n"

                # 显示模板信息
                template_names = []
                for key, value in templates_info.items():
                    if value:
                        template_names.append(f"{key}: {value}")
                if template_names:
                    confirm_msg += "模板设置:\n" + "\n".join(f"  • {name}" for name in template_names) + "\n\n"

                # 显示窗口信息
                if window_info.get("width") and window_info.get("height"):
                    confirm_msg += f"窗口大小: {window_info['width']}x{window_info['height']}\n\n"

                confirm_msg += "是否应用这些设置？"

                if not messagebox.askyesno("确认导入", confirm_msg):
                    return

                # 应用设置
                success_items = []

                # 恢复模板设置
                templates_applied = 0
                for key, value in templates_info.items():
                    if value:
                        setattr(self, key, value)
                        templates_applied += 1

                if templates_applied > 0:
                    success_items.append(f"模板设置 ({templates_applied}项)")

                # 恢复窗口设置（立即应用）
                if window_info.get("width") and window_info.get("height"):
                    self.cache_manager.set_window_geometry(self.root, window_info)
                    success_items.append("窗口大小")

                # 恢复路径设置
                if import_data.get("paths", {}).get("current_package_path"):
                    self.current_package_path = import_data["paths"]["current_package_path"]
                    success_items.append("路径设置")

                # 保存到缓存
                self.save_cache_data()

                # 显示成功信息
                success_msg = "缓存设置导入成功！\n\n已恢复:\n" + "\n".join(f"  • {item}" for item in success_items)
                self.log_message(success_msg)
                messagebox.showinfo("导入成功", success_msg)

            except Exception as e:
                error_msg = f"导入缓存设置失败: {e}"
                self.log_message(error_msg)
                messagebox.showerror("错误", error_msg)

    def run(self):
        """运行主程序"""
        # 启动时自动恢复缓存设置
        self._auto_restore_cache_on_startup()
        self.root.mainloop()

    def _auto_restore_cache_on_startup(self):
        """启动时自动恢复缓存设置"""
        try:
            # 加载缓存数据
            cache_data = self.cache_manager.load_cache()

            # 检查是否有有效的缓存数据
            templates = cache_data.get("templates", {})
            paths = cache_data.get("paths", {})
            window = cache_data.get("window", {})

            restored_items = []

            # 恢复模板设置
            templates_restored = 0
            for key, value in templates.items():
                if value and hasattr(self, key):
                    setattr(self, key, value)
                    templates_restored += 1

            if templates_restored > 0:
                restored_items.append(f"模板设置 ({templates_restored}项)")

            # 恢复路径设置
            if paths.get("current_package_path") and hasattr(self, "current_package_path"):
                self.current_package_path = paths["current_package_path"]
                restored_items.append("材料包路径")

            # 恢复窗口设置
            if window.get("width") and window.get("height"):
                self.cache_manager.set_window_geometry(self.root, window)
                restored_items.append("窗口大小")

            # 如果有恢复的内容，显示提示信息
            if restored_items:
                restored_msg = f"已自动恢复上次设置: {', '.join(restored_items)}"
                self.log_message(f"{restored_msg}")
            else:
                self.log_message("使用默认设置启动")

        except Exception as e:
            # 如果出现任何错误，使用默认设置并记录错误
            self.log_message(f"恢复缓存设置时出错: {e}")
            print(f"启动时恢复缓存失败: {e}")

class TemplateSelectionDialog:
    """模板选择对话框"""
    
    def __init__(self, parent, rule_type_name, master_gui=None, all_rules=None):
        self.dialog = tk.Toplevel(parent)
        self.rule_type_name = rule_type_name
        self.master_gui = master_gui  # 保存主界面引用
        self.all_rules = all_rules  # 保存规则数据引用

        # 根据规则类型名称设置标题和文件夹（使用get_resource_path支持打包后的exe）
        rule_type_mapping = {
            "重命名规则": ("选择重命名模板", get_resource_path("template/rename_templates")),
            "文件夹提取规则": ("选择文件夹提取模板", get_resource_path("template/folder_templates")),
            "Word转PDF规则": ("选择Word转PDF模板", get_resource_path("template/word_to_pdf_templates")),
            "清理规则": ("选择清理模板", get_resource_path("template/clean_templates")),
            "材料包查找规则": ("选择材料包查找模板", get_resource_path("template/data_read_templates"))
        }

        if rule_type_name in rule_type_mapping:
            title, folder = rule_type_mapping[rule_type_name]
            self.dialog.title(title)
            self.template_folder = folder
        else:
            self.dialog.title(f"选择{rule_type_name}")
            self.template_folder = f"template/{rule_type_name.lower()}"

        self.dialog.geometry("450x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.selected_template = None
        self.templates = {}
        self.current_selected_template = None  # 当前已在主界面中选择的模板

        self.load_templates()
        # 获取当前已在主界面中选择的模板
        self.get_current_selected_template()
        self.create_widgets()
    
    def load_templates(self):
        """加载模板文件"""
        import json
        from pathlib import Path
        
        template_dir = Path(self.template_folder)
        if not template_dir.exists():
            return
        
        for json_file in template_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template_key = json_file.stem
                self.templates[template_key] = template_data
            except Exception:
                continue

    def get_current_selected_template(self):
        """获取当前已在主界面中选择的模板"""
        if not self.master_gui:
            return

        try:
            # 从主界面的缓存中获取当前选择的模板
            templates_cache = self.master_gui.cache_data.get("templates", {})

            if self.rule_type_name == "重命名规则":
                self.current_selected_template = templates_cache.get("selected_rename_template")
            elif self.rule_type_name == "文件夹提取规则":
                self.current_selected_template = templates_cache.get("selected_extract_template")
            elif self.rule_type_name == "Word转PDF规则":
                self.current_selected_template = templates_cache.get("selected_word_template")
            elif self.rule_type_name == "清理规则":
                self.current_selected_template = templates_cache.get("selected_clean_template")
            elif self.rule_type_name == "材料包查找规则":
                # 材料包查找规则从传入的all_rules中获取
                if self.all_rules and "材料包查找规则" in self.all_rules and self.all_rules["材料包查找规则"]:
                    first_template = next(iter(self.all_rules["材料包查找规则"].keys()))
                    self.current_selected_template = first_template
                else:
                    self.current_selected_template = None
        except Exception:
            self.current_selected_template = None

    def create_widgets(self):
        """创建对话框组件"""

        # 标题
        title_text = f"请选择{self.rule_type_name}："
        title_label = ttk.Label(self.dialog, text=title_text,
                               font=('Microsoft YaHei', 12, 'bold'))
        title_label.pack(pady=10)
        
        if not self.templates:
            # 没有找到模板，显示友好的提醒信息
            no_template_frame = ttk.Frame(self.dialog)
            no_template_frame.pack(fill='both', expand=True, padx=20, pady=20)

            # 主提醒信息
            main_label = ttk.Label(no_template_frame,
                                  text="未找到可用模板",
                                  font=('Microsoft YaHei', 12, 'bold'),
                                  foreground='orange')
            main_label.pack(pady=(0, 10))

            # 详细信息
            detail_label = ttk.Label(no_template_frame,
                                    text=f"请检查以下位置是否存在模板文件：\n\n{self.template_folder}\n\n"
                                         "可能的解决方案：\n"
                                         "• 检查模板文件夹是否存在\n"
                                         "• 确保模板文件格式正确（JSON）\n"
                                         "• 联系管理员添加相应模板",
                                    font=('Microsoft YaHei', 9),
                                    justify='left')
            detail_label.pack(pady=(0, 20))

            # 操作建议
            suggestion_label = ttk.Label(no_template_frame,
                                        text="建议：\n"
                                             "• 重命名规则：检查 template/rename_templates/\n"
                                             "• 文件夹提取规则：检查 template/folder_templates/\n"
                                             "• Word转PDF规则：检查 template/word_to_pdf_templates/\n"
                                             "• 清理规则：检查 template/clean_templates/\n"
                                             "• 材料包查找规则：检查 template/data_read_templates/",
                                        font=('Microsoft YaHei', 8),
                                        foreground='blue',
                                        justify='left')
            suggestion_label.pack(pady=(0, 20))

            ttk.Button(no_template_frame, text="确定", command=self.cancel_clicked).pack()
            return
        
        # 模板选择区域
        templates_frame = ttk.LabelFrame(self.dialog, text="可用模板", padding=10)
        templates_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        
        # 创建滚动区域
        canvas = tk.Canvas(templates_frame)
        scrollbar = ttk.Scrollbar(templates_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 单选按钮变量
        self.template_var = tk.StringVar()
        
        # 显示模板选项
        for template_key, template_info in self.templates.items():
            # 创建模板选项框架
            template_frame = ttk.Frame(scrollable_frame)
            template_frame.pack(fill='x', pady=5)

            # 单选按钮和模板名称
            rb = ttk.Radiobutton(
                template_frame,
                text=template_info.get('name', template_key),
                variable=self.template_var,
                value=template_key
            )
            rb.pack(anchor='w')

            # 模板描述
            desc_text = template_info.get('description', '无描述')
            desc_label = ttk.Label(
                template_frame,
                text=f"    {desc_text}",
                font=('Microsoft YaHei', 9),
                foreground='gray'
            )
            desc_label.pack(anchor='w', padx=(20, 0))

            # 模板统计信息
            if 'rules' in template_info:
                rule_count = len(template_info['rules'])
                stats_text = f"    包含{rule_count}个规则"
                stats_label = ttk.Label(
                    template_frame,
                    text=stats_text,
                    font=('Microsoft YaHei', 8),
                    foreground='blue'
                )
                stats_label.pack(anchor='w', padx=(20, 0))

        # 默认选择逻辑：优先选择当前已在主界面中选择的模板，如果没有则选择第一个
        if self.current_selected_template and self.current_selected_template in self.templates:
            self.template_var.set(self.current_selected_template)
            print(f"选择当前模板: {self.current_selected_template}")
        elif self.templates:
            # 如果没有当前选择的模板，选择第一个模板
            first_template = next(iter(self.templates.keys()))
            self.template_var.set(first_template)
            print(f"选择第一个模板: {first_template}")
        else:
            # 没有模板的情况已经在上面处理了，这里不应该到达
            print("警告: 没有可用模板")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=20, pady=(10, 20))
        
        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side='right')
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side='right', padx=(0, 10))
    
    def ok_clicked(self):
        """确定按钮点击"""
        selected_key = self.template_var.get()
        if selected_key and selected_key in self.templates:
            self.selected_template = selected_key
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """取消按钮点击"""
        self.selected_template = None
        self.dialog.destroy()

class CheckSelectionDialog:
    """功能检查选择对话框"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("选择检查项目")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 30))
        
        self.selected_checks = []
        self.check_vars = {}
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建对话框组件"""
        
        # 标题
        title_label = ttk.Label(self.dialog, text="请选择要检查的功能模块：", 
                               font=('Microsoft YaHei', 12, 'bold'))
        title_label.pack(pady=10)
        
        # 说明文本
        desc_label = ttk.Label(self.dialog, 
                              text="您可以选择需要检查的特定模块，也可以选择全部进行全面检查。",
                              font=('Microsoft YaHei', 9),
                              foreground='gray')
        desc_label.pack(pady=(0, 10))
        
        # 检查项目选择区域
        checks_frame = ttk.LabelFrame(self.dialog, text="检查项目", padding=10)
        checks_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        
        # 创建滚动区域
        canvas = tk.Canvas(checks_frame)
        scrollbar = ttk.Scrollbar(checks_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 检查项目列表
        check_options = [
            ("Python环境", "Python环境", "检查Python版本和安装状态"),
            ("必需模块", "必需模块", "检查基础Python模块"),
            ("可选模块", "可选模块", "检查可选功能模块（pywin32, PyInstaller）"),
            ("项目模块", "项目模块", "检查本项目的自定义模块"),
            ("目录结构", "目录结构", "检查必需的文件夹结构"),
            ("模板文件", "模板文件", "检查JSON模板文件的格式和完整性"),
            ("数据文件夹", "数据文件夹", "检查data文件夹的内容和结构"),
            ("公司材料包", "公司材料包", "检查公司材料包的结构和完整性"),
            ("ZIP解压功能", "ZIP解压功能", "检查ZIP文件解压和中文编码处理"),
            ("文件夹清理功能", "文件夹清理功能", "检查文件夹清理和整理功能"),
            ("文件夹提取功能", "文件夹提取功能", "检查文件夹提取和模板匹配"),
            ("Word转PDF功能", "Word转PDF功能", "检查Word文档转换PDF功能"),
            ("文件重命名功能", "文件重命名功能", "检查文件重命名和标签添加"),
            ("GUI功能", "GUI功能", "检查图形界面组件和功能")
        ]
        
        for display_name, key, description in check_options:
            var = tk.BooleanVar(value=True)  # 默认全选
            self.check_vars[key] = var
            
            # 创建每个检查项目的框架
            item_frame = ttk.Frame(scrollable_frame)
            item_frame.pack(fill='x', pady=2)
            
            # 复选框和主标题
            main_frame = ttk.Frame(item_frame)
            main_frame.pack(fill='x')
            
            cb = ttk.Checkbutton(main_frame, text=display_name, variable=var)
            cb.pack(anchor='w')
            
            # 描述文本
            desc_label = ttk.Label(item_frame, text=f"    {description}", 
                                  font=('Microsoft YaHei', 8), 
                                  foreground='gray')
            desc_label.pack(anchor='w', padx=(20, 0))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 快捷按钮区域
        quick_frame = ttk.Frame(self.dialog)
        quick_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        ttk.Label(quick_frame, text="快捷操作：").pack(side='left')
        ttk.Button(quick_frame, text="全选", command=self.select_all, width=8).pack(side='left', padx=(10, 5))
        ttk.Button(quick_frame, text="全不选", command=self.select_none, width=8).pack(side='left', padx=5)
        ttk.Button(quick_frame, text="反选", command=self.invert_selection, width=8).pack(side='left', padx=5)
        ttk.Button(quick_frame, text="推荐", command=self.select_recommended, width=8).pack(side='left', padx=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="开始检查", command=self.ok_clicked).pack(side='right')
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side='right', padx=(0, 10))
        
        # 显示统计信息
        self.stats_label = ttk.Label(button_frame, text="", foreground='blue')
        self.stats_label.pack(side='left')
        
        # 初始更新统计
        self.update_stats()
        
        # 绑定事件来更新统计
        for var in self.check_vars.values():
            var.trace('w', lambda *args: self.update_stats())
    
    def update_stats(self):
        """更新选中统计"""
        selected_count = sum(1 for var in self.check_vars.values() if var.get())
        total_count = len(self.check_vars)
        self.stats_label.config(text=f"已选择: {selected_count}/{total_count} 项")
    
    def select_all(self):
        """全选"""
        for var in self.check_vars.values():
            var.set(True)
    
    def select_none(self):
        """全不选"""
        for var in self.check_vars.values():
            var.set(False)
    
    def invert_selection(self):
        """反选"""
        for var in self.check_vars.values():
            var.set(not var.get())
    
    def select_recommended(self):
        """选择推荐项目（常用的检查项目）"""
        recommended = {
            "Python环境", "必需模块", "项目模块", 
            "目录结构", "模板文件", "GUI功能"
        }
        
        for key, var in self.check_vars.items():
            var.set(key in recommended)
    
    def ok_clicked(self):
        """确定按钮点击"""
        self.selected_checks = [key for key, var in self.check_vars.items() if var.get()]
        if not self.selected_checks:
            messagebox.showwarning("警告", "请至少选择一个检查项目！")
            return
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """取消按钮点击"""
        self.selected_checks = []
        self.dialog.destroy()

class CustomFlowDialog:
    """自定义流程选择对话框"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("自定义流程")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.selected_steps = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建对话框组件"""
        
        # 标题
        title_label = ttk.Label(self.dialog, text="请选择要执行的步骤：", 
                               font=('Microsoft YaHei', 12, 'bold'))
        title_label.pack(pady=10)
        
        # 步骤选择区域
        steps_frame = ttk.Frame(self.dialog)
        steps_frame.pack(fill='both', expand=True, padx=20)
        
        self.step_vars = {}
        steps = [
            ("解压ZIP文件", "解压ZIP文件"),
            ("清理文件夹", "清理文件夹"),
            ("Word转PDF", "Word转PDF"),
            ("文件重命名", "文件重命名"),
            ("提取文件夹", "提取文件夹"),
        ]
        
        for display_name, key in steps:
            var = tk.BooleanVar(value=True)
            self.step_vars= var
            ttk.Checkbutton(steps_frame, text=display_name, variable=var).pack(anchor='w', pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="全选", command=self.select_all).pack(side='left')
        ttk.Button(button_frame, text="全不选", command=self.select_none).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side='right')
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side='right', padx=5)
    
    def select_all(self):
        """全选"""
        for var in self.step_vars.values():
            var.set(True)
    
    def select_none(self):
        """全不选"""
        for var in self.step_vars.values():
            var.set(False)
    
    def ok_clicked(self):
        """确定按钮点击"""
        self.selected_steps = [key for key, var in self.step_vars.items() if var.get()]
        if not self.selected_steps:
            messagebox.showwarning("警告", "请至少选择一个步骤！")
            return
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """取消按钮点击"""
        self.selected_steps = []
        self.dialog.destroy()

class PDFMergeDialog:
    """专用的PDF合并管理对话框"""
    
    def __init__(self, parent, main_window=None, log_callback=None):
        # 导入需要的模块
        import os
        self.os = os  # 保存引用以便在方法中使用

        self.main_window = main_window  # 保存主窗口引用
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("PDF合并管理")
        self.dialog.geometry("1024x768")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.log_callback = log_callback
        self.pdf_files = []  # 保存PDF文件列表
        self.selected_files = set()  # 保存选中的文件索引
        self.processor = None  # PDF处理器实例

        self.create_widgets()

        # 检查PyMuPDF支持
        try:
            from pdf_merger import PDFProcessor
            self.processor = PDFProcessor()
            if not self.processor.supported:
                self.show_error("PDF处理功能不可用\n原因: PyMuPDF库未正确加载\n\n解决方案:\n1. 检查PyMuPDF安装: pip install PyMuPDF\n2. 如果是exe版本，请重新构建并确保包含相关依赖")
                self.add_info("PDF处理功能初始化失败")
                self.add_info("请检查PyMuPDF库安装")
            else:
                self.add_info("PDF处理功能已准备就绪")
        except ImportError as e:
            self.show_error(f"无法导入PDF处理模块\n错误: {str(e)}\n\n请确保所有相关文件都在程序目录中")
            self.processor = None
        except Exception as e:
            self.show_error(f"PDF处理功能初始化异常\n错误: {str(e)}")
            self.processor = None
    
    def create_widgets(self):
        """创建对话框组件"""
        
        # 标题区域
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, text="PDF处理工具",
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack()

        subtitle_label = ttk.Label(title_frame, text="支持PDF合并等功能",
                                  font=('Microsoft YaHei', 10))
        subtitle_label.pack()
        
        # 主内容区域
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左侧文件列表区域
        left_frame = ttk.LabelFrame(main_frame, text="PDF文件列表", padding=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # 文件列表（使用Treeview显示）
        columns = ('selected', 'sequence', 'filename', 'pages', 'size')
        self.file_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        self.file_tree.heading('selected', text='选中')
        self.file_tree.heading('sequence', text='顺序')
        self.file_tree.heading('filename', text='文件名')
        self.file_tree.heading('pages', text='页数')
        self.file_tree.heading('size', text='大小')
        
        # 设置列宽度
        self.file_tree.column('selected', width=50, anchor='center')
        self.file_tree.column('sequence', width=50, anchor='center')
        self.file_tree.column('filename', width=250, anchor='w')
        self.file_tree.column('pages', width=60, anchor='center')
        self.file_tree.column('size', width=80, anchor='center')
        
        # 绑定点击事件
        self.file_tree.bind('<Button-1>', self.on_tree_click)
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(left_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        tree_scrollbar.pack(side='right', fill='y')
        
        # 右侧操作区域
        right_frame = ttk.LabelFrame(main_frame, text="操作控制", padding=10)
        right_frame.pack(side='right', fill='y', padx=(5, 0))
        
        # 文件操作按钮
        file_ops_frame = ttk.LabelFrame(right_frame, text="文件操作", padding=5)
        file_ops_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(file_ops_frame, text="➕ 添加文件", 
                  command=self.add_files, width=15).pack(pady=2)
        ttk.Button(file_ops_frame, text="删除选中", 
                  command=self.remove_selected, width=15).pack(pady=2)
        ttk.Button(file_ops_frame, text="清空列表", 
                  command=self.clear_all, width=15).pack(pady=2)
        
        # 选择操作按钮
        select_ops_frame = ttk.LabelFrame(right_frame, text="选择操作", padding=5)
        select_ops_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(select_ops_frame, text="☑️ 全选",
                  command=self.select_all, width=15).pack(pady=2)
        ttk.Button(select_ops_frame, text="☐️ 全不选",
                  command=self.select_none, width=15).pack(pady=2)
        ttk.Button(select_ops_frame, text="反选",
                  command=self.select_invert, width=15).pack(pady=2)


        # 顺序操作按钮
        order_ops_frame = ttk.LabelFrame(right_frame, text="顺序操作", padding=5)
        order_ops_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(order_ops_frame, text="⬆️ 上移",
                  command=self.move_up, width=15).pack(pady=2)
        ttk.Button(order_ops_frame, text="⬇️ 下移",
                  command=self.move_down, width=15).pack(pady=2)
        
        # 分隔线
        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # 合并操作按钮
        merge_ops_frame = ttk.LabelFrame(right_frame, text="合并操作", padding=5)
        merge_ops_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(merge_ops_frame, text="开始合并", 
                  command=self.start_merge, width=15).pack(pady=2)
        
        # 信息显示区域
        info_frame = ttk.LabelFrame(right_frame, text="信息", padding=5)
        info_frame.pack(fill='x', expand=True)
        
        self.info_text = tk.Text(info_frame, height=8, width=25, 
                                font=('Consolas', 9), wrap=tk.WORD)
        info_scrollbar = ttk.Scrollbar(info_frame, orient='vertical', command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side='left', fill='both', expand=True)
        info_scrollbar.pack(side='right', fill='y')
        
        # 底部控制按钮
        bottom_frame = ttk.Frame(self.dialog)
        bottom_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(bottom_frame, text="关闭", command=self.close_dialog).pack(side='right')
        
        # 初始化信息
        self.add_info("欢迎使用PDF处理工具")
        self.add_info("点击'➕ 添加文件'开始添加PDF文件")
    
    def add_info(self, message):
        """添加信息到信息显示区域"""
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.dialog.update_idletasks()
        
        # 同时记录到主程序日志
        if self.log_callback:
            self.log_callback(message)
    
    def show_error(self, message):
        """显示错误信息"""
        messagebox.showerror("错误", message)
        self.add_info(f"{message}")
    
    def add_files(self):
        """添加PDF文件"""
        if not self.processor or not self.processor.supported:
            self.show_error("PDF处理功能不可用")
            return
        
        files = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if not files:
            return
        
        self.add_info(f"正在添加 {len(files)} 个文件...")
        
        added_count = 0
        for file_path in files:
            if self.add_single_file(file_path):
                added_count += 1
        
        if added_count > 0:
            self.add_info(f"成功添加 {added_count} 个文件")
            self.update_file_tree()
            self.update_selection_status()
        else:
            self.add_info("没有添加任何文件")
    
    def add_single_file(self, file_path):
        """添加单个文件"""
        try:
            # 检查文件是否已经存在
            for existing_file in self.pdf_files:
                if existing_file['path'] == file_path:
                    self.add_info(f"文件已存在: {self.os.path.basename(file_path)}")
                    return False
            
            # 获取PDF文件信息
            if self.processor:
                pdf_info = self.processor.get_pdf_info(file_path)
                if pdf_info and 'error' not in pdf_info:
                    file_data = {
                        'path': file_path,
                        'name': pdf_info['file_name'],
                        'pages': pdf_info['page_count'],
                        'size': pdf_info['file_size_formatted']
                    }
                    # 添加文件并默认选中
                    file_index = len(self.pdf_files)
                    self.pdf_files.append(file_data)
                    self.selected_files.add(file_index)
                    return True
                else:
                    error_msg = pdf_info.get('error', '未知错误') if pdf_info else '无法读取文件'
                    self.add_info(f"无效文件: {os.path.basename(file_path)} - {error_msg}")
                    return False
            else:
                self.add_info("PDF处理功能不可用")
                return False
                
        except Exception as e:
            self.add_info(f"处理文件错误: {os.path.basename(file_path)} - {str(e)}")
            return False
    
    def update_file_tree(self):
        """更新文件列表显示"""
        # 清空列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 添加文件
        for i, file_data in enumerate(self.pdf_files):
            # 选中状态显示
            selected_mark = "☑️" if i in self.selected_files else "☐️"
            
            self.file_tree.insert('', 'end', values=(
                selected_mark,
                i + 1,
                file_data['name'],
                file_data['pages'],
                file_data['size']
            ))
    
    def remove_selected(self):
        """删除选中的文件"""
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的文件")
            return
        
        # 获取选中的索引
        indices_to_remove = []
        for item in selected_items:
            index = self.file_tree.index(item)
            indices_to_remove.append(index)
        
        # 从后往前删除，避免索引错位
        for index in sorted(indices_to_remove, reverse=True):
            file_name = self.pdf_files[index]['name']
            del self.pdf_files[index]
            self.add_info(f"已删除: {file_name}")
        
        # 更新选中状态（重新映射索引）
        self.rebuild_selection_indices()
        self.update_file_tree()
        self.update_selection_status()
    
    def clear_all(self):
        """清空所有文件"""
        if not self.pdf_files:
            return
        
        result = messagebox.askyesno("确认", f"确定要清空所有 {len(self.pdf_files)} 个文件吗？")
        if result:
            self.pdf_files.clear()
            self.selected_files.clear()
            self.update_file_tree()
            self.update_selection_status()
            self.add_info("已清空所有文件")
    
    def move_up(self):
        """上移选中的文件"""
        selected_items = self.file_tree.selection()
        if not selected_items or len(selected_items) != 1:
            messagebox.showwarning("警告", "请选择一个文件进行移动")
            return
        
        index = self.file_tree.index(selected_items[0])
        if index == 0:
            messagebox.showinfo("提示", "已经在最顶部")
            return
        
        # 交换位置
        self.pdf_files[index], self.pdf_files[index-1] = self.pdf_files[index-1], self.pdf_files[index]
        
        # 更新选中状态
        if index in self.selected_files:
            self.selected_files.remove(index)
            self.selected_files.add(index-1)
        elif index-1 in self.selected_files:
            self.selected_files.remove(index-1)
            self.selected_files.add(index)
        
        self.update_file_tree()
        
        # 重新选中移动后的文件
        new_item = self.file_tree.get_children()[index-1]
        self.file_tree.selection_set(new_item)
        
        self.add_info(f"⬆️ 已上移: {self.pdf_files[index-1]['name']}")
    
    def move_down(self):
        """下移选中的文件"""
        selected_items = self.file_tree.selection()
        if not selected_items or len(selected_items) != 1:
            messagebox.showwarning("警告", "请选择一个文件进行移动")
            return
        
        index = self.file_tree.index(selected_items[0])
        if index == len(self.pdf_files) - 1:
            messagebox.showinfo("提示", "已经在最底部")
            return
        
        # 交换位置
        self.pdf_files[index], self.pdf_files[index+1] = self.pdf_files[index+1], self.pdf_files[index]
        
        # 更新选中状态
        if index in self.selected_files:
            self.selected_files.remove(index)
            self.selected_files.add(index+1)
        elif index+1 in self.selected_files:
            self.selected_files.remove(index+1)
            self.selected_files.add(index)
        
        self.update_file_tree()
        
        # 重新选中移动后的文件
        new_item = self.file_tree.get_children()[index+1]
        self.file_tree.selection_set(new_item)
        
        self.add_info(f"⬇️ 已下移: {self.pdf_files[index+1]['name']}")
    
    def start_merge(self):
        """开始合并PDF文件"""
        if not self.pdf_files:
            messagebox.showwarning("警告", "请先添加PDF文件")
            return
        
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选中要合并的PDF文件")
            return
        
        if len(self.selected_files) < 2:
            messagebox.showwarning("警告", "至少需要选中两个PDF文件才能合并")
            return
        
        # 选择输出文件
        output_file = filedialog.asksaveasfilename(
            title="保存合并后的PDF文件",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if not output_file:
            return
        
        # 获取选中的文件列表（按索引顺序排列）
        selected_indices = sorted(self.selected_files)
        selected_files_info = [self.pdf_files[i] for i in selected_indices]
        
        # 确认对话框
        file_list = "\n".join([f"{idx+1}. {file_data['name']} ({file_data['pages']}页)" 
                             for idx, file_data in enumerate(selected_files_info)])
        
        total_pages = sum(file_data['pages'] for file_data in selected_files_info)
        
        # 获取文件名用于显示
        output_filename = self.os.path.basename(output_file)
        
        result = messagebox.askyesno("确认合并", 
                                   f"即将合并以下 {len(selected_files_info)} 个选中的PDF文件：\n\n{file_list}\n\n合并后总页数: {total_pages} 页\n输出文件: {output_filename}\n\n是否继续？")
        
        if not result:
            return
        
        # 开始合并
        self.add_info("开始合并选中的PDF文件...")
        
        try:
            # 提取选中文件的路径列表
            file_paths = [file_data['path'] for file_data in selected_files_info]
            
            # 执行合并
            if self.processor:
                success = self.processor.merge_pdfs(file_paths, output_file, self.add_info)
            else:
                success = False
                self.add_info("PDF处理器不可用")
            
            if success:
                self.add_info("PDF合并完成！")
                
                # 显示完成信息
                messagebox.showinfo("完成",
                                   f"PDF合并完成！\n\n输出文件: {self.os.path.basename(output_file)}\n合并了 {len(selected_files_info)} 个文件，共 {total_pages} 页\n\n文件保存位置:\n{self.os.path.dirname(output_file)}")
                self.add_info(f"文件保存位置: {self.os.path.dirname(output_file)}")
            else:
                self.add_info("PDF合并失败")

        except Exception as e:
            error_msg = f"合并过程中发生错误: {str(e)}"
            self.add_info(error_msg)
            messagebox.showerror("错误", error_msg)



    
    def on_tree_click(self, event):
        """处理列表点击事件"""
        # 获取点击的位置
        region = self.file_tree.identify("region", event.x, event.y)
        if region == "cell":
            # 获取点击的行和列
            item_id = self.file_tree.identify_row(event.y)
            column = self.file_tree.identify_column(event.x)
            
            # 如果点击的是第一列（选中列）
            if column == '#1' and item_id:  # '#1' 表示第一列
                # 获取行索引
                try:
                    row_index = self.file_tree.index(item_id)
                    self.toggle_file_selection(row_index)
                except tk.TclError:
                    pass  # 忽略错误
    
    def toggle_file_selection(self, index):
        """切换文件选中状态"""
        if index < len(self.pdf_files):
            if index in self.selected_files:
                self.selected_files.remove(index)
                self.add_info(f"☐️ 取消选中: {self.pdf_files[index]['name']}")
            else:
                self.selected_files.add(index)
                self.add_info(f"☑️ 已选中: {self.pdf_files[index]['name']}")
            
            self.update_file_tree()
            self.update_selection_status()
    
    def select_all(self):
        """全选所有文件"""
        if not self.pdf_files:
            return
        
        self.selected_files = set(range(len(self.pdf_files)))
        self.update_file_tree()
        self.update_selection_status()
        self.add_info(f"☑️ 已全选 {len(self.pdf_files)} 个文件")
    
    def select_none(self):
        """取消选中所有文件"""
        if not self.selected_files:
            return
        
        count = len(self.selected_files)
        self.selected_files.clear()
        self.update_file_tree()
        self.update_selection_status()
        self.add_info(f"☐️ 已取消选中 {count} 个文件")
    
    def select_invert(self):
        """反选文件"""
        if not self.pdf_files:
            return
        
        all_indices = set(range(len(self.pdf_files)))
        self.selected_files = all_indices - self.selected_files
        self.update_file_tree()
        self.update_selection_status()
        self.add_info(f"反选完成，当前选中 {len(self.selected_files)} 个文件")
    
    def update_selection_status(self):
        """更新选中状态信息"""
        total_files = len(self.pdf_files)
        selected_count = len(self.selected_files)
        
        if total_files > 0:
            status_msg = f"当前选中: {selected_count}/{total_files} 个文件"
            if selected_count > 0:
                total_pages = sum(self.pdf_files[i]['pages'] for i in self.selected_files)
                status_msg += f" (共{total_pages}页)"
            self.add_info(status_msg)
    
    def rebuild_selection_indices(self):
        """重新构建选中索引（在删除文件后使用）"""
        # 在删除文件后，需要重新映射选中的索引
        # 简化处理：直接清空选中状态，由用户重新选择
        self.selected_files.clear()
    
    def close_dialog(self):
        """关闭对话框"""
        self.dialog.destroy()

class RuleManagerDialog:
    """统一的规则管理对话框"""

    def __init__(self, master_gui, log_callback=None):
        # master_gui 是主界面对象，从中获取根窗口
        self.master_gui = master_gui
        self.root = master_gui.root  # 获取根窗口

        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("规则管理中心")
        self.dialog.geometry("1024x768")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.root)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 30))

        self.log_callback = log_callback

        # 当前选择的模板（用于规则管理对话框内部）
        self.selected_material_package_template = None

        # 规则数据
        self.all_rules = {
            "重命名规则": {},
            "文件夹提取规则": {},
            "Word转PDF规则": {},
            "清理规则": {},
            "材料包查找规则": {}
        }

        self.load_all_rules()
        self.create_widgets()

    def load_all_rules(self):
        """加载所有规则"""
        import json
        from pathlib import Path

        # 加载重命名规则
        rename_dir = Path(get_resource_path("template/rename_templates"))
        if rename_dir.exists():
            json_files = list(rename_dir.glob("*.json"))
            if self.log_callback:
                self.log_callback(f"发现 {len(json_files)} 个重命名规则文件")
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    self.all_rules["重命名规则"][json_file.stem] = rule_data
                    if self.log_callback:
                        self.log_callback(f"加载重命名规则: {json_file.stem}")
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"加载重命名规则失败 {json_file.name}: {e}")

        # 加载文件夹提取规则
        folder_dir = Path(get_resource_path("template/folder_templates"))
        if folder_dir.exists():
            json_files = list(folder_dir.glob("*.json"))
            if self.log_callback:
                self.log_callback(f"发现 {len(json_files)} 个文件夹提取规则文件")
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    self.all_rules["文件夹提取规则"][json_file.stem] = rule_data
                    if self.log_callback:
                        self.log_callback(f"加载文件夹提取规则: {json_file.stem}")
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"加载文件夹提取规则失败 {json_file.name}: {e}")

        # 加载Word转PDF规则
        word_dir = Path(get_resource_path("template/word_to_pdf_templates"))
        if word_dir.exists():
            json_files = list(word_dir.glob("*.json"))
            if self.log_callback:
                self.log_callback(f"发现 {len(json_files)} 个Word转PDF规则文件")
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    self.all_rules["Word转PDF规则"][json_file.stem] = rule_data
                    if self.log_callback:
                        self.log_callback(f"加载Word转PDF规则: {json_file.stem}")
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"加载Word转PDF规则失败 {json_file.name}: {e}")

        # 加载清理规则
        clean_dir = Path(get_resource_path("template/clean_templates"))
        if clean_dir.exists():
            json_files = list(clean_dir.glob("*.json"))
            if self.log_callback:
                self.log_callback(f"发现 {len(json_files)} 个清理规则文件")
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    self.all_rules["清理规则"][json_file.stem] = rule_data
                    if self.log_callback:
                        self.log_callback(f"加载清理规则: {json_file.stem}")
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"加载清理规则失败 {json_file.name}: {e}")

        # 加载材料包查找规则
        material_package_search_dir = Path(get_resource_path("template/data_read_templates"))
        if material_package_search_dir.exists():
            json_files = list(material_package_search_dir.glob("*.json"))
            if self.log_callback:
                self.log_callback(f"发现 {len(json_files)} 个材料包查找规则文件")
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    self.all_rules["材料包查找规则"][json_file.stem] = rule_data
                    if self.log_callback:
                        self.log_callback(f"加载材料包查找规则: {json_file.stem}")
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"加载材料包查找规则失败 {json_file.name}: {e}")


    def create_widgets(self):
        """创建对话框组件"""

        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 顶部标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))

        title_label = ttk.Label(title_frame, text="规则管理中心",
                               font=('Microsoft YaHei', 16, 'bold'))
        title_label.pack()

        subtitle_label = ttk.Label(title_frame, text="统一管理所有处理规则模板",
                                  font=('Microsoft YaHei', 10))
        subtitle_label.pack()

        # 左侧规则类型选择和控制区域
        left_frame = ttk.LabelFrame(main_frame, text="规则管理面板", padding=10)
        left_frame.pack(side='left', fill='y', padx=(0, 10))

        # 顶部控制区域
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(control_frame, text="刷新规则",
                  command=self.refresh_rules, width=20).pack(side='left', padx=(0, 5))
        ttk.Button(control_frame, text="选择模板",
                  command=self.select_template, width=20).pack(side='left', padx=(0, 5))
        ttk.Button(control_frame, text="编辑规则",
                  command=self.open_rule_editor, width=20).pack(side='left')


        # 规则类型列表
        self.rule_type_listbox = tk.Listbox(left_frame, width=25, height=12,
                                           font=('Microsoft YaHei', 10),
                                           selectmode=tk.SINGLE,
                                           bg='white', selectbackground='#0078D4', selectforeground='white')
        self.rule_type_listbox.pack(fill='both', expand=True)

        # 添加规则类型（带emoji图标）
        rule_types = list(self.all_rules.keys())
        rule_type_icons = {
            "重命名规则": "",
            "文件夹提取规则": "",
            "Word转PDF规则": "",
            "清理规则": "",
            "材料包查找规则": ""
        }

        for i, rule_type in enumerate(rule_types):
            rule_count = len(self.all_rules[rule_type])
            icon = rule_type_icons.get(rule_type, "")
            if i == 0:  # 第一个项目默认选中
                display_text = f"▶ {rule_type} ({rule_count}个规则)"
            else:
                display_text = f"{rule_type} ({rule_count}个规则)"
            self.rule_type_listbox.insert(tk.END, display_text)

        # 绑定选择事件
        self.rule_type_listbox.bind('<<ListboxSelect>>', self.on_rule_type_selected)
        self.rule_type_listbox.selection_set(0)  # 默认选择第一个
        self.current_rule_type = rule_types[0]

        # 底部选中模板显示区域
        self.selected_templates_frame = ttk.LabelFrame(left_frame, text="已选择模板", padding=5)
        self.selected_templates_frame.pack(fill='x', pady=(10, 0))

        # 创建画布用于显示选中模板
        self.templates_canvas = tk.Canvas(self.selected_templates_frame, height=240)
        self.templates_frame = ttk.Frame(self.templates_canvas)

        self.templates_frame.bind(
            "<Configure>",
            lambda e: self.templates_canvas.configure(scrollregion=self.templates_canvas.bbox("all"))
        )

        self.templates_canvas.create_window((0, 0), window=self.templates_frame, anchor="nw")
        self.templates_canvas.pack(side="left", fill="both", expand=True)

        # 右侧规则内容显示
        right_frame = ttk.LabelFrame(main_frame, text="规则内容详情", padding=10)
        right_frame.pack(side='right', fill='both', expand=True)

        # 规则内容文本框
        self.rule_content_text = scrolledtext.ScrolledText(right_frame,
                                                          wrap=tk.WORD,
                                                          font=('Consolas', 9))
        self.rule_content_text.pack(fill='both', expand=True)

        # 底部信息和按钮区域
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill='x', pady=(10, 0))

        # 左侧信息显示（已删除规则统计信息）
        # self.info_label = ttk.Label(bottom_frame,
        #                            text="请选择规则类型查看详细内容",
        #                            font=('Microsoft YaHei', 9))
        # self.info_label.pack(side='left')

        # 初始化显示第一个规则类型的内容
        self.on_rule_type_selected(None)

        # 更新选中模板显示
        self.update_selected_template_display()

    def check_current_templates(self):
        """检查当前选中的模板"""
        if self.log_callback:
            self.log_callback("开始检查当前模板配置...")

        # 检查当前选中的模板 - 从主界面缓存获取模板信息
        try:
            # 获取主界面的模板缓存
            templates_cache = self.master_gui.cache_data.get("templates", {})

            selected_rename = templates_cache.get("selected_rename_template")
            if selected_rename:
                if self.log_callback:
                    self.log_callback(f"重命名规则: {selected_rename}")
            else:
                if self.log_callback:
                    self.log_callback("未选择重命名规则")

            selected_extract = templates_cache.get("selected_extract_template")
            if selected_extract:
                if self.log_callback:
                    self.log_callback(f"提取规则: {selected_extract}")
            else:
                if self.log_callback:
                    self.log_callback("未选择提取规则")

            selected_word = templates_cache.get("selected_word_template")
            if selected_word:
                if self.log_callback:
                    self.log_callback(f"Word转PDF规则: {selected_word}")
            else:
                if self.log_callback:
                    self.log_callback("未选择Word转PDF规则")

            selected_clean = templates_cache.get("selected_clean_template")
            if selected_clean:
                if self.log_callback:
                    self.log_callback(f"清理规则: {selected_clean}")
            else:
                if self.log_callback:
                    self.log_callback("未选择清理规则")
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"检查模板配置时出错: {e}")

        # 检查材料包查找规则（显示可用规则）
        try:
            if "材料包查找规则" in self.all_rules and self.all_rules["材料包查找规则"]:
                rule_count = len(self.all_rules["材料包查找规则"])
                if self.log_callback:
                    self.log_callback(f"材料包查找规则: {rule_count}个可用规则")
            else:
                if self.log_callback:
                    self.log_callback("未找到材料包查找规则")
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"检查材料包规则时出错: {e}")

        if self.log_callback:
            self.log_callback("\n可用规则模板统计:")

        # 显示统计信息
        all_rules = {
            "重命名规则": {},
            "文件夹提取规则": {},
            "Word转PDF规则": {},
            "清理规则": {}
        }

        # 加载规则统计
        import json
        from pathlib import Path

        # 重命名规则
        rename_dir = Path(get_resource_path("template/rename_templates"))
        if rename_dir.exists():
            for json_file in rename_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    all_rules["重命名规则"][json_file.stem] = rule_data
                except:
                    pass

        # 文件夹提取规则
        folder_dir = Path(get_resource_path("template/folder_templates"))
        if folder_dir.exists():
            for json_file in folder_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    all_rules["文件夹提取规则"][json_file.stem] = rule_data
                except:
                    pass

        # Word转PDF规则
        word_dir = Path(get_resource_path("template/word_to_pdf_templates"))
        if word_dir.exists():
            for json_file in word_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    all_rules["Word转PDF规则"][json_file.stem] = rule_data
                except:
                    pass

        # 清理规则
        clean_dir = Path(get_resource_path("template/clean_templates"))
        if clean_dir.exists():
            for json_file in clean_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                    all_rules["清理规则"][json_file.stem] = rule_data
                except:
                    pass

        # 显示统计
        for rule_type, rules in all_rules.items():
            if self.log_callback:
                self.log_callback(f"  {rule_type}: {len(rules)}个可用规则")

        if self.log_callback:
            self.log_callback("规则检查完成")

    def select_template(self):
        """选择模板并应用到全局"""
        current_type = self.current_rule_type
        rules = self.all_rules.get(current_type, {})

        if not rules:
            messagebox.showinfo("提示", f"当前规则类型 {current_type} 没有可用规则")
            return

        # 如果只有一个规则，直接选择
        if len(rules) == 1:
            selected_template = list(rules.keys())[0]
        else:
            # 如果有多个规则，让用户选择
            template_dialog = TemplateSelectionDialog(self.dialog, current_type, self.master_gui, self.all_rules)
            self.dialog.wait_window(template_dialog.dialog)
            selected_template = template_dialog.selected_template

        if selected_template and selected_template in rules:
            # 保存到主界面的缓存
            try:
                # 获取主界面的模板缓存
                templates_cache = self.master_gui.cache_data.get("templates", {})

                if current_type == "重命名规则":
                    templates_cache["selected_rename_template"] = selected_template
                    self.master_gui.selected_rename_template = selected_template  # 同步更新主界面属性
                elif current_type == "文件夹提取规则":
                    templates_cache["selected_extract_template"] = selected_template
                    self.master_gui.selected_extract_template = selected_template  # 同步更新主界面属性
                elif current_type == "Word转PDF规则":
                    templates_cache["selected_word_template"] = selected_template
                    self.master_gui.selected_word_template = selected_template  # 同步更新主界面属性
                elif current_type == "清理规则":
                    templates_cache["selected_clean_template"] = selected_template
                    self.master_gui.selected_clean_template = selected_template  # 同步更新主界面属性
                elif current_type == "材料包查找规则":
                    # 保存材料包查找规则到主界面缓存和变量
                    templates_cache["selected_material_package_template"] = selected_template
                    self.master_gui.selected_material_package_template = selected_template  # 同步更新主界面属性
                    self.selected_material_package_template = selected_template

                # 更新显示
                self.update_selected_template_display()

                # 保存到缓存
                if hasattr(self.master_gui, 'save_cache_data'):
                    self.master_gui.save_cache_data()

                if self.log_callback:
                    self.log_callback(f"已选择模板: {selected_template} (类型: {current_type})")
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"保存模板选择时出错: {e}")

    def update_selected_template_display(self):
        """更新选中模板显示"""
        # 清空现有的模板显示
        for widget in self.templates_frame.winfo_children():
            widget.destroy()

        # 从主界面的缓存中获取模板信息
        try:
            templates_cache = self.master_gui.cache_data.get("templates", {})
            rename_template = templates_cache.get("selected_rename_template")
            extract_template = templates_cache.get("selected_extract_template")
            word_template = templates_cache.get("selected_word_template")
            clean_template = templates_cache.get("selected_clean_template")
            material_package_template = templates_cache.get("selected_material_package_template")
        except:
            rename_template = None
            extract_template = None
            word_template = None
            clean_template = None
            material_package_template = None

        # 如果缓存中没有，则使用对话框中保存的值
        if not material_package_template:
            material_package_template = getattr(self, 'selected_material_package_template', None)

        # 显示选中的模板
        row = 0
        if rename_template:
            self._add_template_item(row, "重命名规则", rename_template)
            row += 1
        if extract_template:
            self._add_template_item(row, "文件夹提取规则", extract_template)
            row += 1
        if word_template:
            self._add_template_item(row, "Word转PDF规则", word_template)
            row += 1
        if clean_template:
            self._add_template_item(row, "清理规则", clean_template)
            row += 1
        if material_package_template:
            self._add_template_item(row, "材料包查找规则", material_package_template)
            row += 1

        # 如果没有选择任何模板，显示提示信息
        if row == 0:
            no_selection_label = ttk.Label(
                self.templates_frame,
                text="暂未选择任何模板",
                font=('Microsoft YaHei', 9, 'italic'),
                foreground='gray'
            )
            no_selection_label.pack(pady=5)

    def _add_template_item(self, row, rule_type, template_name):
        """添加模板显示项"""
        # 规则类型标签
        type_frame = ttk.Frame(self.templates_frame)
        type_frame.grid(row=row, column=0, sticky='w', pady=2)

        type_label = ttk.Label(
            type_frame,
            text=f"{rule_type}:",
            font=('Microsoft YaHei', 9, 'bold'),
            width=15,
            anchor='w'
        )
        type_label.pack(side='left')

        # 截断过长的模板名称
        max_name_length = 20
        display_name = template_name
        if len(template_name) > max_name_length:
            display_name = template_name[:max_name_length-3] + "..."

        # 模板名称标签
        name_label = ttk.Label(
            type_frame,
            text=display_name,
            font=('Microsoft YaHei', 9),
            foreground='blue',
            cursor="hand2"
        )
        # 添加提示文本，显示完整模板名称
        if len(template_name) > max_name_length:
            name_label.bind("<Enter>", lambda e: self._show_tooltip(e, template_name))
            name_label.bind("<Leave>", lambda e: self._hide_tooltip())
        name_label.pack(side='left', padx=(5, 0))

        # 添加点击事件（暂时只显示信息）
        name_label.bind("<Button-1>", lambda e: self._show_template_info(rule_type, template_name))

    def _show_template_info(self, rule_type, template_name):
        """显示模板详细信息"""
        if self.log_callback:
            self.log_callback(f"模板详情: {rule_type} -> {template_name}")

    def _show_tooltip(self, event, text):
        """显示提示文本"""
        # 创建提示窗口
        self.tooltip = tk.Toplevel(self.templates_frame.winfo_toplevel())
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

        label = ttk.Label(self.tooltip, text=text, background="lightyellow",
                         relief="solid", borderwidth=1, font=('Microsoft YaHei', 8))
        label.pack()

    def _hide_tooltip(self):
        """隐藏提示文本"""
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()
            delattr(self, 'tooltip')

    def on_rule_type_selected(self, event):
        """规则类型选择事件"""
        selection = self.rule_type_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        rule_types = list(self.all_rules.keys())
        if index < len(rule_types):
            self.current_rule_type = rule_types[index]

            # 更新规则类型标题（带选中效果）
            rule_count = len(self.all_rules[self.current_rule_type])
            display_text = f"▶ {self.current_rule_type} ({rule_count}个规则)"

            # 先清除所有项目的选中标记
            for i in range(self.rule_type_listbox.size()):
                current_text = self.rule_type_listbox.get(i)
                if current_text.startswith("▶ "):
                    # 移除选中标记，但保留图标
                    clean_text = current_text[2:]
                    self.rule_type_listbox.delete(i)
                    self.rule_type_listbox.insert(i, clean_text)

            # 为当前选中项目添加选中标记
            self.rule_type_listbox.delete(index)
            self.rule_type_listbox.insert(index, display_text)

            # 显示规则内容
            self.display_rule_content()


    def display_rule_content(self):
        """显示当前规则类型的内容"""
        if not hasattr(self, 'current_rule_type'):
            return

        rules = self.all_rules[self.current_rule_type]

        if not rules:
            self.rule_content_text.delete(1.0, tk.END)
            self.rule_content_text.insert(tk.END, f"暂无可用的{self.current_rule_type}")
            # self.info_label.config(text=f"{self.current_rule_type}: 0个规则")
            return

        self.rule_content_text.delete(1.0, tk.END)

        # 显示规则概览
        content_parts = []
        content_parts.append(f"=== {self.current_rule_type} ===")
        content_parts.append(f"共 {len(rules)} 个规则模板：\n")

        # 添加总体统计信息
        if self.log_callback:
            total_rules = sum(len(rule_set) for rule_set in self.all_rules.values())
            self.log_callback(f"规则统计 - {self.current_rule_type}: {len(rules)}/{total_rules} 个规则")

        for i, (rule_name, rule_data) in enumerate(rules.items(), 1):
            rule_info = f"{i}. {rule_data.get('name', rule_name)}\n"

            if 'description' in rule_data:
                rule_info += f"   描述: {rule_data['description']}\n"
            if 'version' in rule_data:
                rule_info += f"   版本: {rule_data['version']}\n"
            if 'author' in rule_data:
                rule_info += f"   作者: {rule_data['author']}\n"
            if 'created_date' in rule_data:
                rule_info += f"   创建日期: {rule_data['created_date']}\n"

            # 显示Word转PDF规则的特殊设置
            if self.current_rule_type == "Word转PDF规则" and 'keep_original_files' in rule_data:
                keep_files = rule_data['keep_original_files']
                rule_info += f"   保留原文件: {'是' if keep_files else '否'}\n"

            # 显示规则的具体内容
            if 'rules' in rule_data:
                rule_info += "   规则内容:\n"
                if self.current_rule_type == "重命名规则":
                    rule_info += self.get_rename_rules_text(rule_data['rules'])
                elif self.current_rule_type == "文件夹提取规则":
                    rule_info += self.get_folder_rules_text(rule_data['rules'])
                elif self.current_rule_type == "Word转PDF规则":
                    rule_info += self.get_word_pdf_rules_text(rule_data['rules'])
                elif self.current_rule_type == "清理规则":
                    rule_info += self.get_clean_rules_text(rule_data['rules'])
                elif self.current_rule_type == "材料包查找规则":
                    rule_info += self.get_clean_rules_text(rule_data['rules'])

            content_parts.append(rule_info)
            content_parts.append("="*50)

        self.rule_content_text.insert(tk.END, "\n".join(content_parts))
        # self.info_label.config(text=f"{self.current_rule_type}: {len(rules)}个规则")

    def get_rename_rules_text(self, rules):
        """获取重命名规则文本"""
        text_parts = []
        for rule_name, rule_config in rules.items():
            text_parts.append(f"     - {rule_name}:")

            # 格式化显示规则配置
            if isinstance(rule_config, dict):
                if 'keywords' in rule_config:
                    keywords = ', '.join(f'"{kw}"' for kw in rule_config['keywords'])
                    text_parts.append(f"       关键词: [{keywords}]")

                if 'folders' in rule_config:
                    folders = ', '.join(f'"{folder}"' for folder in rule_config['folders'])
                    text_parts.append(f"       文件夹: [{folders}]")

                if 'tag' in rule_config:
                    text_parts.append(f"       标签: {rule_config['tag']}")

                if 'prompt' in rule_config:
                    # 截断过长的提示文本
                    prompt = rule_config['prompt']
                    if len(prompt) > 60:
                        prompt = prompt[:57] + "..."
                    text_parts.append(f"       提示: {prompt}")
            else:
                text_parts.append(f"       配置: {rule_config}")

        return "\n".join(text_parts) + "\n"

    def get_folder_rules_text(self, rules):
        """获取文件夹提取规则文本"""
        text_parts = []
        for rule_name, folders in rules.items():
            text_parts.append(f"     - {rule_name}:")
            for folder in folders:
                text_parts.append(f"       - {folder}")
        return "\n".join(text_parts) + "\n"

    def get_word_pdf_rules_text(self, rules):
        """获取Word转PDF规则文本"""
        text_parts = []
        for doc_type, folders in rules.items():
            text_parts.append(f"     - {doc_type}:")
            for folder in folders:
                text_parts.append(f"       - {folder}")
        return "\n".join(text_parts) + "\n"

    def get_clean_rules_text(self, rules):
        """获取清理规则文本"""
        text_parts = []
        for i, rule in enumerate(rules, 1):
            text_parts.append(f"     {i}. 模式: {rule.get('pattern', '未知')}")
            text_parts.append(f"        类型: {rule.get('type', '未知')}")
            if 'description' in rule:
                text_parts.append(f"        描述: {rule['description']}")
        return "\n".join(text_parts) + "\n"


    def refresh_rules(self):
        """刷新所有规则"""
        self.all_rules = {
            "重命名规则": {},
            "文件夹提取规则": {},
            "Word转PDF规则": {},
            "清理规则": {},
            "材料包查找规则": {}
        }
        self.load_all_rules()

        # 规则类型图标
        rule_type_icons = {
            "重命名规则": "",
            "文件夹提取规则": "",
            "Word转PDF规则": "",
            "清理规则": "",
            "材料包查找规则": ""
        }

        # 更新列表显示
        self.rule_type_listbox.delete(0, tk.END)
        rule_types = list(self.all_rules.keys())
        for i, rule_type in enumerate(rule_types):
            rule_count = len(self.all_rules[rule_type])
            icon = rule_type_icons.get(rule_type, "")
            if i == 0:
                display_text = f"▶ {rule_type} ({rule_count}个规则)"
            else:
                display_text = f"{rule_type} ({rule_count}个规则)"
            self.rule_type_listbox.insert(tk.END, display_text)

        self.rule_type_listbox.selection_set(0)
        self.current_rule_type = rule_types[0]
        self.on_rule_type_selected(None)

        if self.log_callback:
            self.log_callback("规则刷新完成")

    def open_rule_editor(self):
        """打开规则编辑器"""
        if not hasattr(self, 'current_rule_type'):
            messagebox.showwarning("警告", "请先选择一个规则类型")
            return

        # 打开规则编辑器对话框
        editor = RuleFileEditorDialog(self.dialog, self.current_rule_type, self.log_callback)
        self.dialog.wait_window(editor.dialog)

        # 如果编辑后需要刷新规则
        if editor.rule_modified:
            self.refresh_rules()

    def close_dialog(self):
        """关闭对话框"""
        self.dialog.destroy()

class RuleEditorDialog:
    """规则编辑对话框"""

    def __init__(self, parent, rule_type, rules, log_callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"编辑{ rule_type }")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 30))

        self.rule_type = rule_type
        self.rules = rules
        self.log_callback = log_callback
        self.rule_modified = False

        # 获取模板文件夹路径（使用get_resource_path支持打包后的exe）
        self.template_dirs = {
            "重命名规则": get_resource_path("template/rename_templates"),
            "文件夹提取规则": get_resource_path("template/folder_templates"),
            "Word转PDF规则": get_resource_path("template/word_to_pdf_templates"),
            "清理规则": get_resource_path("template/clean_templates"),
            "材料包查找规则": get_resource_path("template/data_read_templates")
        }

        self.create_widgets()
        self.load_rule_files()

    def create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 顶部标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))

        title_label = ttk.Label(title_frame, text=f"编辑{self.rule_type}",
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack()

        subtitle_label = ttk.Label(title_frame, text="选择规则文件进行编辑，修改后点击保存",
                                  font=('Microsoft YaHei', 10))
        subtitle_label.pack()

        # 左侧文件选择区域
        left_frame = ttk.LabelFrame(main_frame, text="规则文件", padding=10)
        left_frame.pack(side='left', fill='y', padx=(0, 10))

        # 创建上下分隔的布局
        left_paned = ttk.PanedWindow(left_frame, orient='vertical')
        left_paned.pack(fill='both', expand=True)

        # 上半部分：规则文件列表区域
        top_frame = ttk.Frame(left_paned)
        left_paned.add(top_frame, weight=1)

        # 文件列表
        self.file_listbox = tk.Listbox(top_frame, width=30, height=8,
                                      font=('Microsoft YaHei', 10))
        self.file_listbox.pack(fill='both', expand=True)

        # 绑定选择事件
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_selected)

        # 文件操作按钮
        file_btn_frame = ttk.Frame(top_frame)
        file_btn_frame.pack(fill='x', pady=(5, 0))

        ttk.Button(file_btn_frame, text="刷新列表",
                  command=self.refresh_file_list).pack(side='left', padx=(0, 5))
        ttk.Button(file_btn_frame, text="新建规则",
                  command=self.create_new_rule).pack(side='left', padx=(0, 5))
        ttk.Button(file_btn_frame, text="删除规则",
                  command=self.delete_rule).pack(side='left')

        # 下半部分：状态信息区域
        bottom_frame = ttk.Frame(left_paned)
        left_paned.add(bottom_frame, weight=1)

        # 创建带边框的状态信息区域
        status_container = ttk.LabelFrame(bottom_frame, text="状态信息", padding=5)
        status_container.pack(fill='both', expand=True)

        self.status_label = ttk.Label(status_container, text="就绪",
                                     font=('Microsoft YaHei', 9), width=30)
        self.status_label.pack(side='left', anchor='w', fill='x')

        # 右侧编辑区域
        right_frame = ttk.LabelFrame(main_frame, text="规则编辑器", padding=10)
        right_frame.pack(side='right', fill='both', expand=True)

        # 编辑工具栏
        toolbar_frame = ttk.Frame(right_frame)
        toolbar_frame.pack(fill='x', pady=(0, 10))

        self.current_file_label = ttk.Label(toolbar_frame, text="未选择文件",
                                           font=('Microsoft YaHei', 9))
        self.current_file_label.pack(side='left')

        ttk.Button(toolbar_frame, text="保存",
                  command=self.save_current_file).pack(side='right', padx=(0, 5))
        ttk.Button(toolbar_frame, text="格式化",
                  command=self.format_json).pack(side='right', padx=(0, 5))
        ttk.Button(toolbar_frame, text="验证",
                  command=self.validate_json).pack(side='right')

        # JSON编辑器
        self.json_text = scrolledtext.ScrolledText(right_frame,
                                                  wrap=tk.WORD,
                                                  font=('Consolas', 9))
        self.json_text.pack(fill='both', expand=True)

        # 关闭按钮（移动到右侧底部）
        close_frame = ttk.Frame(right_frame)
        close_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(close_frame, text="关闭",
                  command=self.close_dialog).pack(side='right')

    def load_rule_files(self):
        """加载规则文件列表"""
        self.file_listbox.delete(0, tk.END)

        template_dir = self.template_dirs.get(self.rule_type)
        if not template_dir:
            self.status_label.config(text="错误：未找到规则类型目录")
            return

        from pathlib import Path
        rule_path = Path(template_dir)

        if not rule_path.exists():
            self.status_label.config(text=f"目录不存在：{template_dir}")
            return

        # 查找所有JSON文件
        json_files = list(rule_path.glob("*.json"))
        if not json_files:
            self.status_label.config(text="未找到规则文件")
            return

        for json_file in json_files:
            display_name = f"{json_file.stem}"
            self.file_listbox.insert(tk.END, display_name)

        self.status_label.config(text=f"找到 {len(json_files)} 个规则文件")

    def refresh_file_list(self):
        """刷新文件列表"""
        self.load_rule_files()

    def on_file_selected(self, event):
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        file_index = selection[0]
        file_names = [self.file_listbox.get(i) for i in range(self.file_listbox.size())]

        if file_index < len(file_names):
            selected_name = file_names[file_index]
            self.load_file_content(selected_name)

    def load_file_content(self, file_name):
        """加载文件内容"""
        template_dir = self.template_dirs.get(self.rule_type)
        file_path = Path(template_dir) / f"{file_name}.json"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, content)

            self.current_file_label.config(text=f"当前编辑：{file_name}.json")
            self.status_label.config(text="文件加载成功")

        except Exception as e:
            self.status_label.config(text=f"加载失败：{str(e)}")
            messagebox.showerror("错误", f"无法加载文件：{str(e)}")

    def save_current_file(self):
        """保存当前文件"""
        current_text = self.json_text.get(1.0, tk.END).strip()
        if not current_text:
            messagebox.showwarning("警告", "编辑器为空，无法保存")
            return

        # 获取当前选择的文件名
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要保存的文件")
            return

        file_index = selection[0]
        file_names = [self.file_listbox.get(i) for i in range(self.file_listbox.size())]
        selected_name = file_names[file_index]

        template_dir = self.template_dirs.get(self.rule_type)
        file_path = Path(template_dir) / f"{selected_name}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_text)

            self.status_label.config(text="文件保存成功")
            self.rule_modified = True

            if self.log_callback:
                self.log_callback(f"规则文件已保存：{selected_name}.json")

        except Exception as e:
            self.status_label.config(text=f"保存失败：{str(e)}")
            messagebox.showerror("错误", f"无法保存文件：{str(e)}")

    def format_json(self):
        """格式化JSON"""
        current_text = self.json_text.get(1.0, tk.END).strip()
        if not current_text:
            return

        try:
            import json
            parsed = json.loads(current_text)
            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)

            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, formatted)

            self.status_label.config(text="JSON格式化完成")

        except json.JSONDecodeError as e:
            self.status_label.config(text=f"JSON格式错误：{str(e)}")
            messagebox.showerror("错误", f"JSON格式错误：{str(e)}")
        except Exception as e:
            self.status_label.config(text=f"格式化失败：{str(e)}")

    def validate_json(self):
        """验证JSON模板并显示详细报告"""
        current_text = self.json_text.get(1.0, tk.END).strip()
        if not current_text:
            messagebox.showwarning("警告", "请先输入JSON内容")
            return

        try:
            # 使用专业验证器进行验证
            if validate_template_content:
                validation_report = validate_template_content(current_text, "编辑器内容")
                self.show_validation_report(validation_report)
            else:
                # 退回基础验证
                import json
                parsed = json.loads(current_text)

                if not isinstance(parsed, dict):
                    raise ValueError("JSON必须是对象类型")

                missing_fields = []
                if 'name' not in parsed:
                    missing_fields.append('name')
                if 'description' not in parsed:
                    missing_fields.append('description')

                if missing_fields:
                    messagebox.showwarning("验证建议",
                        f"建议添加以下字段：\n{', '.join(missing_fields)}")

                self.status_label.config(text="基础验证通过")

        except json.JSONDecodeError as e:
            error_msg = f"JSON格式错误：第{e.lineno}行，{e.msg}"
            self.status_label.config(text=error_msg)
            self.show_json_error_dialog(error_msg, e)
        except Exception as e:
            self.status_label.config(text=f"验证失败：{str(e)}")
            messagebox.showerror("错误", f"验证过程中发生错误：\n\n{str(e)}")

    def show_validation_report(self, report_text):
        """显示详细的验证报告对话框"""
        # 创建验证报告对话框
        report_window = tk.Toplevel(self.master)
        report_window.title("模板验证报告")
        report_window.geometry("800x600")
        report_window.transient(self.master)
        report_window.grab_set()

        # 设置窗口图标（如果有的话）
        try:
            report_window.iconbitmap(self.icon_path)
        except:
            pass

        # 创建主框架
        main_frame = ttk.Frame(report_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题标签
        title_label = ttk.Label(main_frame,
                               text="企业文档模板验证报告",
                               font=("微软雅黑", 14, "bold"),
                               foreground="#2E8B57")
        title_label.pack(pady=(0, 10))

        # 创建文本区域和滚动条
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建文本区域
        report_text_widget = tk.Text(text_frame,
                                   wrap=tk.WORD,
                                   yscrollcommand=scrollbar.set,
                                   font=("Consolas", 10),
                                   padx=10,
                                   pady=10)
        report_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置滚动条
        scrollbar.config(command=report_text_widget.yview)

        # 插入验证报告
        report_text_widget.insert(tk.END, report_text)
        report_text_widget.config(state=tk.DISABLED)  # 设置为只读

        # 为不同类型的内容设置颜色
        self._colorize_validation_report(report_text_widget, report_text)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def copy_report():
            """复制报告到剪贴板"""
            try:
                import pyperclip
                pyperclip.copy(report_text)
                messagebox.showinfo("提示", "验证报告已复制到剪贴板")
            except ImportError:
                # 如果没有pyperclip，使用tkinter自带的剪贴板
                report_text_widget.config(state=tk.NORMAL)
                content = report_text_widget.get(1.0, tk.END)
                report_text_widget.config(state=tk.DISABLED)
                self.master.clipboard_clear()
                self.master.clipboard_append(content.strip())
                self.master.update()
                messagebox.showinfo("提示", "验证报告已复制到剪贴板")

        def save_report():
            """保存报告到文件"""
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存验证报告"
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report_text)
                    messagebox.showinfo("成功", f"验证报告已保存到：\n{file_path}")
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败：{str(e)}")

        # 按钮
        ttk.Button(button_frame, text="复制报告",
                  command=copy_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="保存报告",
                  command=save_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="关闭",
                  command=report_window.destroy).pack(side=tk.RIGHT)

        # 居中显示窗口
        report_window.update_idletasks()
        x = (report_window.winfo_screenwidth() - report_window.winfo_width()) // 2
        y = (report_window.winfo_screenheight() - report_window.winfo_height()) // 2
        report_window.geometry(f"+{x}+{y}")

    def _colorize_validation_report(self, text_widget, report_text):
        """设置验证报告样式（纯黑色文本）"""
        # 不使用颜色标签，保持纯黑色文本显示
        pass

    def show_json_error_dialog(self, error_msg, original_error):
        """显示JSON错误对话框"""
        error_window = tk.Toplevel(self.master)
        error_window.title("JSON格式错误")
        error_window.geometry("600x400")
        error_window.transient(self.master)
        error_window.grab_set()

        # 主框架
        main_frame = ttk.Frame(error_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 错误图标和标题
        error_title_frame = ttk.Frame(main_frame)
        error_title_frame.pack(fill=tk.X, pady=(0, 10))

        error_label = ttk.Label(error_title_frame,
                               text="JSON格式错误",
                               font=("微软雅黑", 16, "bold"),
                               foreground="#DC143C")
        error_label.pack()

        # 错误详情
        details_frame = ttk.LabelFrame(main_frame, text="错误详情", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 创建文本区域显示错误信息
        error_text = tk.Text(details_frame, wrap=tk.WORD, height=8, font=("微软雅黑", 10))
        error_text.pack(fill=tk.BOTH, expand=True)
        error_text.insert(tk.END, f"错误信息：{error_msg}\n\n")
        error_text.insert(tk.END, f"原始错误：{str(original_error)}\n\n")
        error_text.insert(tk.END, "常见解决方案：\n")
        error_text.insert(tk.END, "• 检查引号是否正确配对\n")
        error_text.insert(tk.END, "• 检查逗号是否正确放置\n")
        error_text.insert(tk.END, "• 检查括号是否正确闭合\n")
        error_text.insert(tk.END, "• 确认所有字符串都用双引号包围\n")
        error_text.config(state=tk.DISABLED)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def go_to_error_line():
            """跳转到错误行"""
            # 这里可以添加跳转到错误行的逻辑
            error_window.destroy()
            messagebox.showinfo("提示", "请检查JSON编辑器中的对应行")

        ttk.Button(button_frame, text="转到错误行",
                  command=go_to_error_line).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="复制错误",
                  command=lambda: self.copy_to_clipboard(error_msg)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="关闭",
                  command=error_window.destroy).pack(side=tk.RIGHT)

        # 居中显示
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() - error_window.winfo_width()) // 2
        y = (error_window.winfo_screenheight() - error_window.winfo_height()) // 2
        error_window.geometry(f"+{x}+{y}")

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            import pyperclip
            pyperclip.copy(text)
            messagebox.showinfo("提示", "文本已复制到剪贴板")
        except ImportError:
            # 如果没有pyperclip，使用tkinter自带的剪贴板
            self.master.clipboard_clear()
            self.master.clipboard_append(text)
            self.master.update()
            messagebox.showinfo("提示", "文本已复制到剪贴板")

    def create_new_rule(self):
        """新建规则"""
        # 创建新规则对话框
        dialog = tk.Toplevel(self.dialog)
        dialog.title("新建规则")
        dialog.geometry("400x200")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # 居中显示
        dialog.geometry("+%d+%d" % (self.dialog.winfo_rootx() + 100, self.dialog.winfo_rooty() + 100))

        # 规则名称输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(name_frame, text="规则名称：").pack(side='left')
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side='left', padx=(10, 0))

        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=10)

        def create_rule():
            rule_name = name_var.get().strip()
            if not rule_name:
                messagebox.showwarning("警告", "请输入规则名称")
                return

            # 检查是否已存在
            template_dir = self.template_dirs.get(self.rule_type)
            file_path = Path(template_dir) / f"{rule_name}.json"

            if file_path.exists():
                messagebox.showwarning("警告", f"规则文件已存在：{rule_name}.json")
                return

            # 创建基础JSON结构
            base_structure = self.get_base_rule_structure()

            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(base_structure, f, ensure_ascii=False, indent=2)

                self.refresh_file_list()

                # 自动选择新创建的文件
                for i in range(self.file_listbox.size()):
                    if self.file_listbox.get(i) == rule_name:
                        self.file_listbox.selection_set(i)
                        self.load_file_content(rule_name)
                        break

                self.status_label.config(text=f"新规则已创建：{rule_name}")
                dialog.destroy()

                if self.log_callback:
                    self.log_callback(f"新规则已创建：{rule_name}.json")

            except Exception as e:
                messagebox.showerror("错误", f"创建规则失败：{str(e)}")

        ttk.Button(btn_frame, text="创建", command=create_rule).pack(side='right', padx=(0, 5))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='right')

    def get_base_rule_structure(self):
        """获取基础规则结构"""
        if self.rule_type == "重命名规则":
            return {
                "name": "新重命名规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": {
                    "示例规则": "示例模式"
                }
            }
        elif self.rule_type == "文件夹提取规则":
            return {
                "name": "新文件夹提取规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": [
                    {
                        "pattern": "*示例*",
                        "type": "folder",
                        "description": "示例规则"
                    }
                ]
            }
        elif self.rule_type == "Word转PDF规则":
            return {
                "name": "新Word转PDF规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": {
                    "示例文档类型": ["示例文件夹路径"]
                },
                "keep_original_files": True
            }
        elif self.rule_type == "清理规则":
            return {
                "name": "新清理规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": [
                    {
                        "pattern": "示例模式",
                        "type": "folder",
                        "description": "示例规则"
                    }
                ]
            }
        else:
            return {
                "name": "新规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户"
            }

    def delete_rule(self):
        """删除规则"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的规则")
            return

        file_index = selection[0]
        file_names = [self.file_listbox.get(i) for i in range(self.file_listbox.size())]
        selected_name = file_names[file_index]

        # 确认删除
        result = messagebox.askyesno("确认删除",
                                   f"确定要删除规则文件：{selected_name}.json 吗？\n\n此操作不可撤销！")

        if not result:
            return

        template_dir = self.template_dirs.get(self.rule_type)
        file_path = Path(template_dir) / f"{selected_name}.json"

        try:
            if file_path.exists():
                file_path.unlink()
                self.refresh_file_list()
                self.json_text.delete(1.0, tk.END)
                self.current_file_label.config(text="未选择文件")
                self.status_label.config(text=f"规则已删除：{selected_name}")

                if self.log_callback:
                    self.log_callback(f"规则已删除：{selected_name}.json")
            else:
                self.status_label.config(text="文件不存在")

        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{str(e)}")

    def close_dialog(self):
        """关闭对话框"""
        self.dialog.destroy()


class RuleFileEditorDialog:
    """规则文件编辑器对话框"""

    def __init__(self, parent, rule_type, log_callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"编辑{rule_type}")
        self.dialog.geometry("1000x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 30))

        self.rule_type = rule_type
        self.log_callback = log_callback
        self.rule_modified = False

        # 获取模板文件夹路径（使用get_resource_path支持打包后的exe）
        self.template_dirs = {
            "重命名规则": get_resource_path("template/rename_templates"),
            "文件夹提取规则": get_resource_path("template/folder_templates"),
            "Word转PDF规则": get_resource_path("template/word_to_pdf_templates"),
            "清理规则": get_resource_path("template/clean_templates"),
            "材料包查找规则": get_resource_path("template/data_read_templates")
        }

        self.create_widgets()
        self.load_rule_files()

    def create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 顶部标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))

        title_label = ttk.Label(title_frame, text=f"编辑{self.rule_type}",
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack()

        subtitle_label = ttk.Label(title_frame, text="选择规则文件进行编辑，修改后点击保存",
                                  font=('Microsoft YaHei', 10))
        subtitle_label.pack()

        # 左侧文件选择区域
        left_frame = ttk.LabelFrame(main_frame, text="规则文件", padding=10)
        left_frame.pack(side='left', fill='y', padx=(0, 10))

        # 创建上下分隔的布局
        left_paned = ttk.PanedWindow(left_frame, orient='vertical')
        left_paned.pack(fill='both', expand=True)

        # 上半部分：规则文件列表区域
        top_frame = ttk.Frame(left_paned)
        left_paned.add(top_frame, weight=1)

        # 文件列表
        self.file_listbox = tk.Listbox(top_frame, width=30, height=8,
                                      font=('Microsoft YaHei', 10))
        self.file_listbox.pack(fill='both', expand=True)

        # 绑定选择事件
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_selected)

        # 文件操作按钮
        file_btn_frame = ttk.Frame(top_frame)
        file_btn_frame.pack(fill='x', pady=(5, 0))

        ttk.Button(file_btn_frame, text="刷新",
                  command=self.refresh_file_list).pack(side='left', padx=(0, 5))
        ttk.Button(file_btn_frame, text="新建",
                  command=self.create_new_file).pack(side='left', padx=(0, 5))
        ttk.Button(file_btn_frame, text="删除",
                  command=self.delete_file).pack(side='left')

        # 下半部分：状态信息区域
        bottom_frame = ttk.Frame(left_paned)
        left_paned.add(bottom_frame, weight=1)

        # 创建带边框的状态信息区域
        status_container = ttk.LabelFrame(bottom_frame, text="状态信息", padding=5)
        status_container.pack(fill='both', expand=True)

        self.status_label = ttk.Label(status_container, text="就绪",
                                     font=('Microsoft YaHei', 9), width=30)
        self.status_label.pack(side='left', anchor='w', fill='x')

        # 右侧编辑区域
        right_frame = ttk.LabelFrame(main_frame, text="规则编辑器", padding=10)
        right_frame.pack(side='right', fill='both', expand=True)

        # 编辑工具栏
        toolbar_frame = ttk.Frame(right_frame)
        toolbar_frame.pack(fill='x', pady=(0, 10))

        self.current_file_label = ttk.Label(toolbar_frame, text="未选择文件",
                                           font=('Microsoft YaHei', 9))
        self.current_file_label.pack(side='left')

        ttk.Button(toolbar_frame, text="保存",
                  command=self.save_current_file).pack(side='right', padx=(0, 5))
        ttk.Button(toolbar_frame, text="格式化",
                  command=self.format_json).pack(side='right', padx=(0, 5))
        ttk.Button(toolbar_frame, text="验证",
                  command=self.validate_json).pack(side='right')

        # JSON编辑器
        self.json_text = scrolledtext.ScrolledText(right_frame,
                                                  wrap=tk.WORD,
                                                  font=('Consolas', 9))
        self.json_text.pack(fill='both', expand=True)

        # 关闭按钮（移动到右侧底部）
        close_frame = ttk.Frame(right_frame)
        close_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(close_frame, text="关闭",
                  command=self.close_dialog).pack(side='right')

    def load_rule_files(self):
        """加载规则文件列表"""
        self.file_listbox.delete(0, tk.END)

        template_dir = self.template_dirs.get(self.rule_type)
        if not template_dir:
            self.status_label.config(text="错误：未找到规则类型目录")
            return

        from pathlib import Path
        rule_path = Path(template_dir)

        if not rule_path.exists():
            self.status_label.config(text=f"目录不存在：{template_dir}")
            return

        # 查找所有JSON文件
        json_files = list(rule_path.glob("*.json"))
        if not json_files:
            self.status_label.config(text="未找到规则文件")
            return

        for json_file in json_files:
            display_name = f"{json_file.stem}"
            self.file_listbox.insert(tk.END, display_name)

        self.status_label.config(text=f"找到 {len(json_files)} 个规则文件")

    def refresh_file_list(self):
        """刷新文件列表"""
        self.load_rule_files()

    def on_file_selected(self, event):
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        file_index = selection[0]
        file_names = [self.file_listbox.get(i) for i in range(self.file_listbox.size())]

        if file_index < len(file_names):
            selected_name = file_names[file_index]
            self.load_file_content(selected_name)

    def load_file_content(self, file_name):
        """加载文件内容"""
        template_dir = self.template_dirs.get(self.rule_type)
        file_path = Path(template_dir) / f"{file_name}.json"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, content)

            self.current_file_label.config(text=f"当前编辑：{file_name}.json")
            self.status_label.config(text="文件加载成功")

        except Exception as e:
            self.status_label.config(text=f"加载失败：{str(e)}")
            messagebox.showerror("错误", f"无法加载文件：{str(e)}")

    def save_current_file(self):
        """保存当前文件"""
        current_text = self.json_text.get(1.0, tk.END).strip()
        if not current_text:
            messagebox.showwarning("警告", "编辑器为空，无法保存")
            return

        # 获取当前选择的文件名
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要保存的文件")
            return

        file_index = selection[0]
        file_names = [self.file_listbox.get(i) for i in range(self.file_listbox.size())]
        selected_name = file_names[file_index]

        template_dir = self.template_dirs.get(self.rule_type)
        file_path = Path(template_dir) / f"{selected_name}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_text)

            self.status_label.config(text="文件保存成功")
            self.rule_modified = True

            if self.log_callback:
                self.log_callback(f"规则文件已保存：{selected_name}.json")

        except Exception as e:
            self.status_label.config(text=f"保存失败：{str(e)}")
            messagebox.showerror("错误", f"无法保存文件：{str(e)}")

    def format_json(self):
        """格式化JSON"""
        current_text = self.json_text.get(1.0, tk.END).strip()
        if not current_text:
            return

        try:
            import json
            parsed = json.loads(current_text)
            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)

            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, formatted)

            self.status_label.config(text="JSON格式化完成")

        except json.JSONDecodeError as e:
            self.status_label.config(text=f"JSON格式错误：{str(e)}")
            messagebox.showerror("错误", f"JSON格式错误：{str(e)}")
        except Exception as e:
            self.status_label.config(text=f"格式化失败：{str(e)}")

    def validate_json(self):
        """验证JSON模板并显示详细报告"""
        current_text = self.json_text.get(1.0, tk.END).strip()
        if not current_text:
            messagebox.showwarning("警告", "请先输入JSON内容")
            return

        try:
            # 使用专业验证器进行验证
            if validate_template_content:
                validation_report = validate_template_content(current_text, "编辑器内容")
                self.show_validation_report(validation_report)
            else:
                # 退回基础验证
                import json
                parsed = json.loads(current_text)

                if not isinstance(parsed, dict):
                    raise ValueError("JSON必须是对象类型")

                missing_fields = []
                if 'name' not in parsed:
                    missing_fields.append('name')
                if 'description' not in parsed:
                    missing_fields.append('description')

                if missing_fields:
                    messagebox.showwarning("验证建议",
                        f"建议添加以下字段：\n{', '.join(missing_fields)}")

                self.status_label.config(text="基础验证通过")

        except json.JSONDecodeError as e:
            error_msg = f"JSON格式错误：第{e.lineno}行，{e.msg}"
            self.status_label.config(text=error_msg)
            self.show_json_error_dialog(error_msg, e)
        except Exception as e:
            self.status_label.config(text=f"验证失败：{str(e)}")
            messagebox.showerror("错误", f"验证过程中发生错误：\n\n{str(e)}")

    def delete_file(self):
        """删除文件"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的规则文件")
            return

        file_index = selection[0]
        file_names = [self.file_listbox.get(i) for i in range(self.file_listbox.size())]
        selected_name = file_names[file_index]

        # 确认删除
        result = messagebox.askyesno("确认删除",
                                   f"确定要删除规则文件：{selected_name}.json 吗？\n\n此操作不可撤销！")

        if not result:
            return

        template_dir = self.template_dirs.get(self.rule_type)
        file_path = Path(template_dir) / f"{selected_name}.json"

        try:
            if file_path.exists():
                file_path.unlink()
                self.refresh_file_list()
                self.json_text.delete(1.0, tk.END)
                self.current_file_label.config(text="未选择文件")
                self.status_label.config(text=f"规则已删除：{selected_name}")

                if self.log_callback:
                    self.log_callback(f"规则已删除：{selected_name}.json")
            else:
                self.status_label.config(text="文件不存在")

        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{str(e)}")

    def create_new_file(self):
        """新建规则文件"""
        # 创建新规则对话框
        dialog = tk.Toplevel(self.dialog)
        dialog.title("新建规则")
        dialog.geometry("400x200")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # 居中显示
        dialog.geometry("+%d+%d" % (self.dialog.winfo_rootx() + 100, self.dialog.winfo_rooty() + 100))

        # 规则名称输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(name_frame, text="规则名称：").pack(side='left')
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side='left', padx=(10, 0))

        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=10)

        def create_rule():
            rule_name = name_var.get().strip()
            if not rule_name:
                messagebox.showwarning("警告", "请输入规则名称")
                return

            # 检查是否已存在
            template_dir = self.template_dirs.get(self.rule_type)
            file_path = Path(template_dir) / f"{rule_name}.json"

            if file_path.exists():
                messagebox.showwarning("警告", f"规则文件已存在：{rule_name}.json")
                return

            # 创建基础JSON结构
            base_structure = self.get_base_rule_structure()

            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(base_structure, f, ensure_ascii=False, indent=2)

                self.refresh_file_list()

                # 自动选择新创建的文件
                for i in range(self.file_listbox.size()):
                    if self.file_listbox.get(i) == rule_name:
                        self.file_listbox.selection_set(i)
                        self.load_file_content(rule_name)
                        break

                dialog.destroy()

                if self.log_callback:
                    self.log_callback(f"新规则已创建：{rule_name}.json")

            except Exception as e:
                messagebox.showerror("错误", f"创建失败：{str(e)}")

        ttk.Button(btn_frame, text="创建",
                  command=create_rule).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="取消",
                  command=dialog.destroy).pack(side='left')

        # 设置焦点
        name_entry.focus()

    def get_base_rule_structure(self):
        """获取基础规则结构"""
        if self.rule_type == "重命名规则":
            return {
                "name": "新重命名规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": {
                    "示例规则": "示例模式"
                }
            }
        elif self.rule_type == "文件夹提取规则":
            return {
                "name": "新文件夹提取规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": [
                    {
                        "pattern": "*示例*",
                        "type": "folder",
                        "description": "示例规则"
                    }
                ]
            }
        elif self.rule_type == "Word转PDF规则":
            return {
                "name": "新Word转PDF规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": {
                    "示例文档类型": ["示例文件夹路径"]
                },
                "keep_original_files": True
            }
        elif self.rule_type == "清理规则":
            return {
                "name": "新清理规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": [
                    {
                        "pattern": "示例模式",
                        "type": "folder",
                        "description": "示例规则"
                    }
                ]
            }
        elif self.rule_type == "材料包查找规则":
            return {
                "name": "新材料包查找规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户",
                "rules": {
                    "示例规则": "示例模式"
                }
            }
        else:
            return {
                "name": "新规则",
                "description": "请输入规则描述",
                "version": "1.0.0",
                "author": "用户"
            }

    def show_validation_report(self, report_text):
        """显示详细的验证报告对话框"""
        # 创建验证报告对话框
        report_window = tk.Toplevel(self.dialog)
        report_window.title("模板验证报告")
        report_window.geometry("800x600")
        report_window.transient(self.dialog)
        report_window.grab_set()

        # 创建主框架
        main_frame = ttk.Frame(report_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题标签
        title_label = ttk.Label(main_frame,
                               text="企业文档模板验证报告",
                               font=("微软雅黑", 14, "bold"),
                               foreground="#2E8B57")
        title_label.pack(pady=(0, 10))

        # 创建文本区域和滚动条
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建文本区域
        report_text_widget = tk.Text(text_frame,
                                   wrap=tk.WORD,
                                   yscrollcommand=scrollbar.set,
                                   font=("Consolas", 10),
                                   padx=10,
                                   pady=10)
        report_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置滚动条
        scrollbar.config(command=report_text_widget.yview)

        # 插入验证报告
        report_text_widget.insert(tk.END, report_text)
        report_text_widget.config(state=tk.DISABLED)  # 设置为只读

        # 为不同类型的内容设置颜色
        self._colorize_validation_report(report_text_widget, report_text)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def copy_report():
            """复制报告到剪贴板"""
            try:
                import pyperclip
                pyperclip.copy(report_text)
                messagebox.showinfo("提示", "验证报告已复制到剪贴板")
            except ImportError:
                # 如果没有pyperclip，使用tkinter自带的剪贴板
                report_text_widget.config(state=tk.NORMAL)
                content = report_text_widget.get(1.0, tk.END)
                report_text_widget.config(state=tk.DISABLED)
                self.dialog.clipboard_clear()
                self.dialog.clipboard_append(content.strip())
                self.dialog.update()
                messagebox.showinfo("提示", "验证报告已复制到剪贴板")

        def save_report():
            """保存报告到文件"""
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存验证报告"
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report_text)
                    messagebox.showinfo("成功", f"验证报告已保存到：\n{file_path}")
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败：{str(e)}")

        # 按钮
        ttk.Button(button_frame, text="复制报告",
                  command=copy_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="保存报告",
                  command=save_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="关闭",
                  command=report_window.destroy).pack(side=tk.RIGHT)

        # 居中显示窗口
        report_window.update_idletasks()
        x = (report_window.winfo_screenwidth() - report_window.winfo_width()) // 2
        y = (report_window.winfo_screenheight() - report_window.winfo_height()) // 2
        report_window.geometry(f"+{x}+{y}")

    def _colorize_validation_report(self, text_widget, report_text):
        """设置验证报告样式（纯黑色文本）"""
        # 不使用颜色标签，保持纯黑色文本显示
        pass

    def show_json_error_dialog(self, error_msg, original_error):
        """显示JSON错误对话框"""
        error_window = tk.Toplevel(self.dialog)
        error_window.title("JSON格式错误")
        error_window.geometry("600x400")
        error_window.transient(self.dialog)
        error_window.grab_set()

        # 主框架
        main_frame = ttk.Frame(error_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 错误图标和标题
        error_title_frame = ttk.Frame(main_frame)
        error_title_frame.pack(fill=tk.X, pady=(0, 10))

        error_label = ttk.Label(error_title_frame,
                               text="JSON格式错误",
                               font=("微软雅黑", 16, "bold"),
                               foreground="#DC143C")
        error_label.pack()

        # 错误详情
        details_frame = ttk.LabelFrame(main_frame, text="错误详情", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 创建文本区域显示错误信息
        error_text = tk.Text(details_frame, wrap=tk.WORD, height=8, font=("微软雅黑", 10))
        error_text.pack(fill=tk.BOTH, expand=True)
        error_text.insert(tk.END, f"错误信息：{error_msg}\n\n")
        error_text.insert(tk.END, f"原始错误：{str(original_error)}\n\n")
        error_text.insert(tk.END, "常见解决方案：\n")
        error_text.insert(tk.END, "• 检查引号是否正确配对\n")
        error_text.insert(tk.END, "• 检查逗号是否正确放置\n")
        error_text.insert(tk.END, "• 检查括号是否正确闭合\n")
        error_text.insert(tk.END, "• 确认所有字符串都用双引号包围\n")
        error_text.config(state=tk.DISABLED)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def go_to_error_line():
            """跳转到错误行"""
            # 这里可以添加跳转到错误行的逻辑
            error_window.destroy()
            messagebox.showinfo("提示", "请检查JSON编辑器中的对应行")

        ttk.Button(button_frame, text="转到错误行",
                  command=go_to_error_line).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="复制错误",
                  command=lambda: self.copy_to_clipboard(error_msg)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="关闭",
                  command=error_window.destroy).pack(side=tk.RIGHT)

        # 居中显示
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() - error_window.winfo_width()) // 2
        y = (error_window.winfo_screenheight() - error_window.winfo_height()) // 2
        error_window.geometry(f"+{x}+{y}")

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            import pyperclip
            pyperclip.copy(text)
            messagebox.showinfo("提示", "文本已复制到剪贴板")
        except ImportError:
            # 如果没有pyperclip，使用tkinter自带的剪贴板
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(text)
            self.dialog.update()
            messagebox.showinfo("提示", "文本已复制到剪贴板")

    def close_dialog(self):
        """关闭对话框"""
        self.dialog.destroy()


def main():
    """主函数"""
    try:
        app = MedicalDocProcessor()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
    