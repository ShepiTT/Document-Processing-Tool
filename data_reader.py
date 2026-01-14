"""
数据读取模块
用于从医疗器械申报材料文件夹中智能读取和提取特定类型的文档

更新时间：2025-10-15
"""

import os
import sys
import json
import shutil
import fnmatch
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

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

class DataReaderEngine:
    """数据读取引擎"""

    def __init__(self, template_path: str = None):
        """
        初始化数据读取引擎

        Args:
            template_path: 模板文件路径，如果为None则使用默认模板
        """
        self.template_path = template_path or get_resource_path("template/data_read_templates/医疗器械通用读取模板.json")
        self.template_data = None
        self.read_results = {}
        self.load_template()

    def load_template(self) -> bool:
        """
        加载读取模板

        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(self.template_path):
                logging.error(f"模板文件不存在: {self.template_path}")
                return False

            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template_data = json.load(f)

            logging.info(f"成功加载模板: {self.template_data.get('name', '未知')}")
            return True

        except Exception as e:
            logging.error(f"加载模板失败: {e}")
            return False

    def read_from_package(self, package_path: str, output_base: str = "output") -> Dict[str, List[Dict[str, Any]]]:
        """
        从材料包中读取文件

        Args:
            package_path: 材料包路径
            output_base: 输出基础文件夹

        Returns:
            Dict[str, List[Dict]]: 读取结果，键为规则名称，值为文件信息列表
        """
        if not self.template_data:
            logging.error("模板未加载")
            return {}

        if not os.path.exists(package_path):
            logging.error(f"材料包路径不存在: {package_path}")
            return {}

        read_rules = self.template_data.get('read_rules', [])
        read_options = self.template_data.get('read_options', {})

        self.read_results = {}

        # 按规则顺序处理（保持模板中的顺序）
        for rule_config in read_rules:
            rule_name = rule_config.get('pattern', '未知规则')
            results = self._read_single_rule(rule_name, rule_config, package_path, output_base, read_options)
            if results:
                self.read_results[rule_name] = results
                logging.info(f"规则 '{rule_name}' 读取 {len(results)} 个文件")

        return self.read_results

    def _read_single_rule(self, rule_name: str, rule_config: Dict, package_path: str,
                         output_base: str, read_options: Dict) -> List[Dict[str, Any]]:
        """
        读取单个规则

        Args:
            rule_name: 规则名称
            rule_config: 规则配置
            package_path: 材料包路径
            output_base: 输出基础文件夹
            read_options: 读取选项

        Returns:
            List[Dict]: 读取的文件列表
        """
        results = []

        # 获取规则参数
        keywords = rule_config.get('keywords', [])
        file_extensions = rule_config.get('extensions', [])
        folders = rule_config.get('source_folders', [])
        multiple_files = rule_config.get('allow_multiple', False)
        required = rule_config.get('required', False)
        output_folder = rule_config.get('output_folder', rule_name)

        # 读取选项
        min_file_size = read_options.get('min_file_size', 1024)
        exclude_temp_files = read_options.get('exclude_temp_files', True)
        preserve_structure = read_options.get('preserve_structure', False)
        naming_conflicts = read_options.get('naming_conflicts', 'rename')
        create_company_folders = read_options.get('create_company_folders', True)
        case_sensitive = read_options.get('case_sensitive', False)
        max_files = read_options.get('max_files', 100)

        # 遍历指定的文件夹
        for folder_path in folders:
            full_folder_path = Path(package_path) / folder_path

            if not full_folder_path.exists():
                continue

            # 递归搜索文件
            for file_path in full_folder_path.rglob('*'):
                if not file_path.is_file():
                    continue

                # 检查文件大小
                if file_path.stat().st_size < min_file_size:
                    continue

                # 检查排除模式
                filename = file_path.name
                if exclude_temp_files:
                    # 排除临时文件和系统文件
                    exclude_patterns = ["~$*", "*.tmp", "临时文件*"]
                    if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns):
                        continue

                # 检查文件扩展名
                if file_extensions:
                    if not any(filename.lower().endswith(ext.lower()) for ext in file_extensions):
                        continue

                # 检查关键词
                if keywords:
                    found_keyword = False
                    for keyword in keywords:
                        if case_sensitive:
                            if keyword in filename:
                                found_keyword = True
                                break
                        else:
                            if keyword.lower() in filename.lower():
                                found_keyword = True
                                break

                    if not found_keyword:
                        continue

                # 生成输出文件名（简化命名）
                company_name = Path(package_path).name
                # 简单命名：原文件名（如果有冲突会自动重命名）
                output_name = filename

                # 生成输出路径
                if create_company_folders:
                    output_dir = Path(output_base) / company_name / output_folder
                else:
                    output_dir = Path(output_base) / output_folder

                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / output_name

                # 处理命名冲突
                if output_file.exists():
                    if naming_conflicts == 'rename':
                        output_file = self._resolve_name_conflict(output_file)
                    elif naming_conflicts == 'skip':
                        continue
                    # 'overwrite' 直接覆盖

                # 复制文件
                try:
                    shutil.copy2(file_path, output_file)

                    file_info = {
                        'source_path': str(file_path),
                        'output_path': str(output_file),
                        'file_name': file_path.name,
                        'file_size': file_path.stat().st_size,
                        'company': company_name,
                        'rule': rule_name,
                        'matched_keyword': next((kw for kw in keywords if kw.lower() in filename.lower()), None) if keywords else None
                    }

                    results.append(file_info)

                    # 如果不允许多个文件，提前结束
                    if not multiple_files and len(results) >= 1:
                        return results

                    # 检查最大文件数
                    if len(results) >= max_files:
                        logging.warning(f"规则 '{rule_name}' 达到最大文件数限制: {max_files}")
                        return results

                except Exception as e:
                    logging.error(f"复制文件失败 {file_path} -> {output_file}: {e}")

        return results


    def _resolve_name_conflict(self, target_path: Path) -> Path:
        """
        解决命名冲突

        Args:
            target_path: 目标路径

        Returns:
            Path: 解决冲突后的路径
        """
        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent

        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
            if counter > 999:  # 防止无限循环
                break

        return target_path

    def get_read_summary(self) -> Dict[str, Any]:
        """
        获取读取结果摘要

        Returns:
            Dict: 读取摘要信息
        """
        if not self.read_results:
            return {'total_rules': 0, 'total_files': 0, 'rules': []}

        total_files = sum(len(files) for files in self.read_results.values())

        summary = {
            'total_rules': len(self.read_results),
            'total_files': total_files,
            'rules': []
        }

        for rule_name, files in self.read_results.items():
            # 在模板中查找对应的规则配置
            rule_config = None
            for rule in self.template_data.get('read_rules', []):
                if rule.get('pattern') == rule_name:
                    rule_config = rule
                    break

            summary['rules'].append({
                'rule_name': rule_name,
                'file_count': len(files),
                'required': rule_config.get('required', False) if rule_config else False
            })

        return summary

    def export_read_log(self, output_path: str = "data_read_log.json") -> bool:
        """
        导出读取日志

        Args:
            output_path: 输出文件路径

        Returns:
            bool: 是否导出成功
        """
        try:
            export_data = {
                'template_info': {
                    'name': self.template_data.get('name', '未知'),
                    'version': self.template_data.get('version', '未知'),
                    'read_time': str(Path.cwd())
                },
                'read_results': self.read_results,
                'summary': self.get_read_summary()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logging.info(f"读取日志已导出到: {output_path}")
            return True

        except Exception as e:
            logging.error(f"导出读取日志失败: {e}")
            return False


class DataReaderDialog:
    """数据读取对话框"""

    def __init__(self, parent, log_callback=None):
        """
        初始化数据读取对话框

        Args:
            parent: 父窗口
            log_callback: 日志回调函数
        """
        self.parent = parent
        self.log_callback = log_callback
        self.reader_engine = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("数据读取工具")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.create_widgets()

    def create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 顶部控制区域
        control_frame = ttk.LabelFrame(main_frame, text="📖 读取控制", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))

        # 模板选择
        template_frame = ttk.Frame(control_frame)
        template_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(template_frame, text="读取模板:").pack(side='left')
        self.template_combo = ttk.Combobox(template_frame, state='readonly', width=50)
        self.template_combo.pack(side='left', padx=(10, 0), fill='x', expand=True)

        ttk.Button(template_frame, text="选择模板",
                  command=self.select_template).pack(side='left', padx=(10, 0))

        # 材料包选择
        package_frame = ttk.Frame(control_frame)
        package_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(package_frame, text="材料包:").pack(side='left')
        self.package_combo = ttk.Combobox(package_frame, state='readonly', width=50)
        self.package_combo.pack(side='left', padx=(10, 0), fill='x', expand=True)

        ttk.Button(package_frame, text="扫描材料包",
                  command=self.scan_packages).pack(side='left', padx=(10, 0))

        # 输出设置
        output_frame = ttk.Frame(control_frame)
        output_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(output_frame, text="输出文件夹:").pack(side='left')
        self.output_entry = ttk.Entry(output_frame, width=50)
        self.output_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        self.output_entry.insert(0, "output")

        ttk.Button(output_frame, text="浏览",
                  command=self.browse_output).pack(side='left', padx=(10, 0))

        # 操作按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x')

        ttk.Button(button_frame, text="开始读取",
                  command=self.start_read).pack(side='left')

        ttk.Button(button_frame, text="导出日志",
                  command=self.export_log).pack(side='left', padx=(10, 0))

        ttk.Button(button_frame, text="清除结果",
                  command=self.clear_results).pack(side='left', padx=(10, 0))

        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="📊 读取结果", padding=10)
        result_frame.pack(fill='both', expand=True)

        # 结果统计
        self.stats_label = ttk.Label(result_frame, text="未开始读取")
        self.stats_label.pack(anchor='w', pady=(0, 10))

        # 结果表格
        columns = ('rule_name', 'file_count', 'required', 'status')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=10)

        # 设置列标题和宽度
        self.result_tree.heading('rule_name', text='规则名称')
        self.result_tree.heading('file_count', text='文件数量')
        self.result_tree.heading('required', text='必需')
        self.result_tree.heading('status', text='状态')

        self.result_tree.column('rule_name', width=200)
        self.result_tree.column('file_count', width=100, anchor='center')
        self.result_tree.column('required', width=80, anchor='center')
        self.result_tree.column('status', width=100, anchor='center')

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)

        self.result_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 文件列表区域
        file_frame = ttk.LabelFrame(main_frame, text="📄 文件列表", padding=10)
        file_frame.pack(fill='both', expand=True)

        # 文件列表
        file_columns = ('source_path', 'output_path', 'file_name', 'file_size', 'company', 'rule')
        self.file_tree = ttk.Treeview(file_frame, columns=file_columns, show='headings', height=8)

        # 设置列标题和宽度
        self.file_tree.heading('source_path', text='源文件路径')
        self.file_tree.heading('output_path', text='输出路径')
        self.file_tree.heading('file_name', text='文件名')
        self.file_tree.heading('file_size', text='大小(KB)')
        self.file_tree.heading('company', text='公司')
        self.file_tree.heading('rule', text='规则')

        self.file_tree.column('source_path', width=250)
        self.file_tree.column('output_path', width=250)
        self.file_tree.column('file_name', width=150)
        self.file_tree.column('file_size', width=80, anchor='center')
        self.file_tree.column('company', width=100)
        self.file_tree.column('rule', width=100)

        # 文件列表滚动条
        file_scrollbar = ttk.Scrollbar(file_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)

        self.file_tree.pack(side='left', fill='both', expand=True)
        file_scrollbar.pack(side='right', fill='y')

        # 绑定选择事件
        self.result_tree.bind('<<TreeviewSelect>>', self.on_rule_selected)
        self.file_tree.bind('<Double-1>', self.on_file_double_click)

        # 加载模板和材料包列表
        self.load_templates()
        self.scan_packages()

    def load_templates(self):
        """加载可用模板"""
        template_dir = Path(get_resource_path("template/data_read_templates"))
        if template_dir.exists():
            template_files = list(template_dir.glob("*.json"))
            template_names = [f.stem for f in template_files]

            if template_names:
                self.template_combo['values'] = template_names
                self.template_combo.set(template_names[0])  # 默认选择第一个
            else:
                if self.log_callback:
                    self.log_callback("未找到任何数据读取模板")

    def scan_packages(self):
        """扫描材料包（根据模板规则）"""
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
                if self.log_callback:
                    self.log_callback("未找到data文件夹")
                return

            # 获取当前选择的模板
            selected_template = self.template_combo.get()
            if selected_template:
                template_path = get_resource_path(f"template/data_read_templates/{selected_template}.json")
                if os.path.exists(template_path):
                    # 加载模板获取匹配规则
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        folder_patterns = self._get_folder_patterns_from_template(template_data)
                    except:
                        folder_patterns = ["*材料包"]  # 默认模式
                else:
                    folder_patterns = ["*材料包"]  # 默认模式
            else:
                folder_patterns = ["*材料包"]  # 默认模式

            package_dirs = []
            # 先扫描一级目录
            for item in data_path.iterdir():
                if item.is_dir() and self._match_folder_patterns(item.name, folder_patterns):
                    package_dirs.append((item.name, str(item)))

            # 如果一级目录没找到，再扫描二级目录
            if not package_dirs:
                for item in data_path.iterdir():
                    if item.is_dir():
                        for sub_item in item.iterdir():
                            if sub_item.is_dir() and self._match_folder_patterns(sub_item.name, folder_patterns):
                                package_dirs.append((sub_item.name, str(sub_item)))

            if package_dirs:
                package_names = [name for name, path in package_dirs]
                self.package_combo['values'] = package_names
                self.package_combo.set(package_names[0])  # 默认选择第一个
                if self.log_callback:
                    self.log_callback(f"发现 {len(package_dirs)} 个文件夹")
            else:
                if self.log_callback:
                    self.log_callback("未找到匹配的文件夹")

        except Exception as e:
            if self.log_callback:
                self.log_callback(f"扫描文件夹失败: {e}")

    def _get_folder_patterns_from_template(self, template_data: dict) -> List[str]:
        """
        从模板中提取文件夹匹配模式
        
        Args:
            template_data: 模板数据
            
        Returns:
            List[str]: 文件夹匹配模式列表
        """
        patterns = []
        rules = template_data.get('rules', [])
        
        for rule in rules:
            if rule.get('type') == 'folder':
                pattern = rule.get('pattern', '')
                if pattern:
                    patterns.append(pattern)
        
        # 如果没有找到文件夹规则，返回默认模式
        if not patterns:
            patterns = ["*材料包"]
        
        return patterns
    
    def _match_folder_patterns(self, folder_name: str, patterns: List[str]) -> bool:
        """
        检查文件夹名是否匹配任一模式
        
        Args:
            folder_name: 文件夹名称
            patterns: 匹配模式列表
            
        Returns:
            bool: 是否匹配
        """
        for pattern in patterns:
            if fnmatch.fnmatch(folder_name, pattern):
                return True
        return False

    def select_template(self):
        """选择模板文件"""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="选择数据读取模板",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialdir=get_resource_path("template/data_read_templates")
        )

        if file_path:
            # 更新下拉框
            template_name = Path(file_path).stem
            current_values = list(self.template_combo['values'])
            if template_name not in current_values:
                current_values.append(template_name)
                self.template_combo['values'] = current_values
            self.template_combo.set(template_name)
            
            # 重新扫描材料包（使用新模板的规则）
            self.scan_packages()

    def browse_output(self):
        """浏览输出文件夹"""
        from tkinter import filedialog

        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        if folder_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder_path)

    def start_read(self):
        """开始读取"""
        selected_template = self.template_combo.get()
        selected_package = self.package_combo.get()
        output_folder = self.output_entry.get().strip()

        if not selected_template:
            messagebox.showwarning("警告", "请选择一个读取模板")
            return

        if not selected_package:
            messagebox.showwarning("警告", "请选择一个材料包")
            return

        if not output_folder:
            messagebox.showwarning("警告", "请输入输出文件夹")
            return

        # 构造模板路径
        template_path = get_resource_path(f"template/data_read_templates/{selected_template}.json")

        if not os.path.exists(template_path):
            messagebox.showerror("错误", f"模板文件不存在: {template_path}")
            return

        # 构造材料包路径
        possible_paths = [
            Path("data"),
            Path("./data"),
            Path(os.getcwd()) / "data"
        ]

        package_path = None
        for path in possible_paths:
            if path.exists() and path.is_dir():
                # 先找一级目录
                test_path = path / selected_package
                if test_path.exists():
                    package_path = str(test_path)
                    break

                # 再找二级目录
                for item in path.iterdir():
                    if item.is_dir():
                        test_path = item / selected_package
                        if test_path.exists():
                            package_path = str(test_path)
                            break
                if package_path:
                    break

        if not package_path:
            messagebox.showerror("错误", f"材料包不存在: {selected_package}")
            return

        # 创建读取引擎并执行读取
        self.reader_engine = DataReaderEngine(template_path)

        if self.log_callback:
            self.log_callback(f"开始使用模板 '{selected_template}' 读取材料包 '{selected_package}'...")

        try:
            results = self.reader_engine.read_from_package(package_path, output_folder)

            # 显示结果
            self.display_read_results(results)

            # 显示统计信息
            summary = self.reader_engine.get_read_summary()
            self.stats_label.config(text=f"共读取 {summary['total_files']} 个文件，来自 {summary['total_rules']} 个规则")

            if self.log_callback:
                self.log_callback(f"读取完成，共读取 {summary['total_files']} 个文件")

        except Exception as e:
            error_msg = f"读取过程中发生错误: {str(e)}"
            if self.log_callback:
                self.log_callback(error_msg)
            messagebox.showerror("错误", error_msg)

    def display_read_results(self, results: Dict[str, List[Dict[str, Any]]]):
        """显示读取结果"""
        # 清空现有结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if not results:
            self.stats_label.config(text="未读取到任何文件")
            return

        # 显示规则结果
        for rule_name, files in results.items():
            # 在模板中查找对应的规则配置
            rule_config = None
            for rule in self.reader_engine.template_data.get('read_rules', []):
                if rule.get('pattern') == rule_name:
                    rule_config = rule
                    break

            is_required = rule_config.get('required', False) if rule_config else False
            status = "必需" if is_required else "可选"

            self.result_tree.insert('', 'end', values=(
                rule_name,
                len(files),
                status,
                "✓" if files else "✗"
            ))

    def on_rule_selected(self, event):
        """规则选择事件"""
        selection = self.result_tree.selection()
        if not selection:
            return

        item = selection[0]
        rule_name = self.result_tree.item(item, 'values')[0]

        # 显示该规则的文件列表
        self.display_rule_files(rule_name)

    def display_rule_files(self, rule_name: str):
        """显示规则的文件列表"""
        # 清空文件列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if not self.reader_engine or rule_name not in self.reader_engine.read_results:
            return

        files = self.reader_engine.read_results[rule_name]

        for file_info in files:
            file_size_kb = file_info['file_size'] // 1024
            self.file_tree.insert('', 'end', values=(
                file_info['source_path'],
                file_info['output_path'],
                file_info['file_name'],
                f"{file_size_kb} KB",
                file_info['company'],
                file_info['rule']
            ))

    def on_file_double_click(self, event):
        """文件双击事件"""
        selection = self.file_tree.selection()
        if not selection:
            return

        item = selection[0]
        output_path = self.file_tree.item(item, 'values')[1]

        # 在文件管理器中打开输出文件夹
        try:
            os.startfile(os.path.dirname(output_path))
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"打开文件夹失败: {e}")

    def export_log(self):
        """导出读取日志"""
        if not self.reader_engine:
            messagebox.showwarning("警告", "请先执行读取")
            return

        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            title="导出读取日志",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialfile="data_read_log.json"
        )

        if file_path:
            if self.reader_engine.export_read_log(file_path):
                messagebox.showinfo("成功", f"日志已导出到: {file_path}")
            else:
                messagebox.showerror("错误", "导出失败")

    def clear_results(self):
        """清除读取结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        self.stats_label.config(text="未开始读取")
        self.reader_engine = None


# 如果直接运行此模块，则启动测试
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.title("数据读取工具测试")

    def test_callback(message):
        print(f"[LOG] {message}")

    dialog = DataReaderDialog(root, test_callback)
    root.mainloop()
