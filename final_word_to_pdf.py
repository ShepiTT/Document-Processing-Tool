#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版Office文档和图片转PDF转换器 - 增强版
修复了路径问题和兼容性问题
新增图片转PDF功能，支持批量和单文件转换
移除了删除原文件的逻辑，保留所有原始文件
自动检测并优先使用WPS Office，支持Microsoft Office Word回退

作者：Lxx
更新时间：2025-10-20
"""

import os
import sys
import json
from pathlib import Path
import win32com.client
import pythoncom

from path_helper import get_resource_path, get_app_path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARNING]  PIL (Pillow) 库未安装，图片转换功能将不可用")
    print("[TIP] 请安装: pip install Pillow")

class FinalWordToPDFConverter:
    """最终版Office转PDF转换器（自动检测WPS/Microsoft Office）"""

    def __init__(self, template_path=None):
        self.word_app = None
        self.template_path = template_path
        self.template_data = None
        self.use_template = template_path is not None
        self.keep_original_files = True  # 默认保留原文件

        if self.use_template:
            self.load_template()

    def load_template(self):
        """加载转换模板"""
        print(f"[DEBUG] 开始加载模板文件: {self.template_path}")
        print(f"[DEBUG] 文件是否存在: {os.path.exists(self.template_path)}")
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template_data = json.load(f)
            print(f"[OK] 已加载转换模板: {self.template_data.get('name', '未知模板')}")
            
            # 显示模板规则信息
            rules = self.template_data.get('rules', {})
            print(f"[INFO] 模板包含 {len(rules)} 条规则:")
            for rule_name, patterns in list(rules.items())[:3]:  # 只显示前3条
                print(f"  - {rule_name}: {patterns}")
            if len(rules) > 3:
                print(f"  ... 还有 {len(rules) - 3} 条规则")

            # 读取保留原文件设置
            self.keep_original_files = self.template_data.get('keep_original_files', True)
            print(f"[INFO] 保留原文件设置: {'是' if self.keep_original_files else '否'}")
            print(f"[DEBUG] use_template 设置为: True")
        except FileNotFoundError:
            print(f"[ERROR] 模板文件不存在: {self.template_path}")
            print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
            self.template_data = None
            self.use_template = False
        except json.JSONDecodeError as e:
            print(f"[ERROR] 模板文件格式错误: {self.template_path}")
            print(f"[ERROR] JSON解析错误: {e}")
            self.template_data = None
            self.use_template = False
        except Exception as e:
            print(f"[ERROR] 加载模板时出错: {e}")
            import traceback
            print(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
            self.template_data = None
            self.use_template = False

    def file_matches_template(self, file_path):
        """检查文件是否匹配模板中的任一规则"""
        if not self.use_template or not self.template_data:
            print(f"[DEBUG] 无模板或模板数据为空，返回True (匹配所有文件)")
            return True  # 无模板时匹配所有文件

        file_path_obj = Path(file_path)
        # 统一使用正斜杠格式的路径字符串，避免Windows路径分隔符问题
        file_path_str = str(file_path_obj).replace('\\', '/')
        file_name = file_path_obj.name
        
        # 获取所有规则
        rules = self.template_data.get("rules", {})

        for rule_name, patterns in rules.items():
            # patterns 可能是一个字符串或数组
            if isinstance(patterns, list):
                pattern_list = patterns
            else:
                pattern_list = [patterns]

            for pattern in pattern_list:
                # 同样统一使用正斜杠
                pattern_normalized = pattern.replace('\\', '/')
                
                # 检查路径模式是否在文件路径的任何位置出现
                if pattern_normalized in file_path_str:
                    print(f"[MATCH] [OK] 文件匹配规则 '{rule_name}': {file_name}")
                    print(f"        模式: {pattern_normalized}")
                    print(f"        路径: {file_path_str}")
                    return True

        # 没有匹配任何规则
        print(f"[SKIP] [ERROR] 文件不匹配任何规则: {file_name}")
        print(f"       完整路径: {file_path_str}")
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_word_app()

    def detect_available_office_apps(self):
        """检测系统中可用的Office应用程序"""
        available_apps = []
        app_info = {}

        # 检查WPS Office
        try:
            pythoncom.CoInitialize()
            wps_app = win32com.client.Dispatch("KWPS.Application")
            wps_app.Visible = False
            wps_app.DisplayAlerts = False

            # 获取版本信息
            version = wps_app.Version
            app_info['WPS'] = {
                'name': 'WPS Office',
                'prog_id': 'KWPS.Application',
                'version': version,
                'priority': 1  # 优先级最高
            }
            available_apps.append('WPS')

            # 关闭临时连接
            wps_app.Quit()
            try:
                pythoncom.CoUninitialize()
            except:
                pass

            print(f"[DETECT] [OK] 检测到WPS Office (版本: {version})")

        except Exception as e:
            print(f"[DETECT] [ERROR] WPS Office不可用: {e}")
            try:
                pythoncom.CoUninitialize()
            except:
                pass

        # 检查Microsoft Office Word
        try:
            pythoncom.CoInitialize()
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = False

            # 获取版本信息
            version = word_app.Version
            app_info['MS_WORD'] = {
                'name': 'Microsoft Office Word',
                'prog_id': 'Word.Application',
                'version': version,
                'priority': 2  # 优先级较低
            }
            available_apps.append('MS_WORD')

            # 关闭临时连接
            word_app.Quit()
            try:
                pythoncom.CoUninitialize()
            except:
                pass

            print(f"[DETECT] [OK] 检测到Microsoft Office Word (版本: {version})")

        except Exception as e:
            print(f"[DETECT] [ERROR] Microsoft Office Word不可用: {e}")
            try:
                pythoncom.CoUninitialize()
            except:
                pass

        return available_apps, app_info

    def initialize_word_app(self):
        """初始化Office应用程序（优先使用WPS）"""
        try:
            pythoncom.CoInitialize()

            # 检测可用应用程序
            available_apps, app_info = self.detect_available_office_apps()

            if not available_apps:
                print("[ERROR] 未检测到任何可用的Office应用程序")
                print("[TIP] 请安装WPS Office或Microsoft Office")
                self.word_app = None
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass
                return False

            # 选择优先级最高的应用程序
            selected_app = None
            selected_key = None

            # 优先选择WPS
            for app_key in available_apps:
                if app_key == 'WPS':
                    selected_app = app_info[app_key]
                    selected_key = app_key
                    break
            else:
                # 如果没有WPS，选择优先级最高的可用应用程序
                available_apps.sort(key=lambda x: app_info[x]['priority'])
                selected_key = available_apps[0]
                selected_app = app_info[selected_key]

            print(f"[INFO] 选择使用: {selected_app['name']} (版本: {selected_app['version']})")

            # 启动选定的应用程序
            self.word_app = win32com.client.Dispatch(selected_app['prog_id'])
            self.word_app.Visible = False
            self.word_app.DisplayAlerts = False

            print(f"[OK] {selected_app['name']} 初始化成功")
            return True

        except Exception as e:
            print(f"[ERROR] 初始化Office应用程序失败: {e}")
            print(f"[DEBUG] 错误详情: {type(e).__name__}: {str(e)}")
            self.word_app = None
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            return False

    def close_word_app(self):
        """安全关闭Office应用程序"""
        if not self.word_app:
            return

        try:
            # 检查应用程序是否仍然可用
            if not self._is_app_alive():
                print("[DISCONNECT] Office应用程序连接已断开")
                self.word_app = None
                return

            # 关闭所有文档
            try:
                for doc in self.word_app.Documents:
                    try:
                        doc.Close(False)
                    except Exception as doc_error:
                        print(f"[WARNING] 关闭文档时出错: {doc_error}")
            except Exception as docs_error:
                print(f"[WARNING] 访问文档集合时出错: {docs_error}")

            # 退出应用程序
            self.word_app.Quit()
            print("[OK] Office应用程序已关闭")

        except Exception as e:
            print(f"[WARNING] 关闭应用程序时出错: {e}")
        finally:
            self.word_app = None
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def _is_app_alive(self):
        """检查应用程序是否仍然存活"""
        if not self.word_app:
            return False
        try:
            _ = self.word_app.Version
            return True
        except:
            return False

    def convert_single_file(self, word_file, pdf_file=None):
        """转换单个Office文件为PDF"""
        if not self.word_app:
            print("[ERROR] Office应用程序未初始化")
            return False

        try:
            # 检查文件是否存在
            word_path = Path(word_file)
            if not word_path.exists():
                print(f"[ERROR] 文件不存在: {word_file}")
                return False

            # 获取绝对路径
            abs_word_path = word_path.resolve()

            # 设置输出路径
            if pdf_file is None:
                pdf_file = word_path.with_suffix('.pdf')
            pdf_path = Path(pdf_file)
            abs_pdf_path = pdf_path.resolve()

            # 确保输出目录存在
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"[REFRESH] 正在转换: {word_path.name}")
            print(f"[DIR] 源文件路径: {abs_word_path}")
            print(f"[DIR] 输出路径: {abs_pdf_path}")

            # 打开文档
            print("[READ] 正在打开文档...")
            doc = self.word_app.Documents.Open(str(abs_word_path))

            # 转换为PDF
            print("[FILE] 正在转换为PDF...")
            doc.ExportAsFixedFormat(str(abs_pdf_path), 17)  # 17 = PDF格式

            # 关闭文档
            doc.Close(False)

            # 验证PDF是否生成
            if abs_pdf_path.exists():
                file_size = abs_pdf_path.stat().st_size
                print(f"[OK] 转换成功! 文件大小: {file_size} bytes")

                # 根据设置决定是否删除原文件
                if not self.keep_original_files:
                    try:
                        abs_word_path.unlink()
                        print(f"[DELETE] 已删除原文件: {word_path.name}")
                    except Exception as e:
                        print(f"[WARNING] 删除原文件失败: {e}")
                else:
                    print(f"[SAVE] 保留原文件: {word_path.name}")

                return True
            else:
                print("[ERROR] PDF文件生成失败")
                return False

        except Exception as e:
            print(f"[ERROR] 转换失败: {e}")
            return False

    def convert_image_to_pdf(self, image_file, pdf_file=None):
        """转换单个图片文件为PDF"""
        if not PIL_AVAILABLE:
            print("[ERROR] PIL库不可用，无法进行图片转换")
            print("[TIP] 请安装Pillow: pip install Pillow")
            return False

        try:
            # 检查文件是否存在
            image_path = Path(image_file)
            if not image_path.exists():
                print(f"[ERROR] 图片文件不存在: {image_file}")
                return False

            # 获取绝对路径
            abs_image_path = image_path.resolve()

            # 设置输出路径
            if pdf_file is None:
                pdf_file = image_path.with_suffix('.pdf')
            pdf_path = Path(pdf_file)
            abs_pdf_path = pdf_path.resolve()

            # 确保输出目录存在
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"[REFRESH] 正在转换图片: {image_path.name}")
            print(f"[DIR] 源文件路径: {abs_image_path}")
            print(f"[DIR] 输出路径: {abs_pdf_path}")

            # 打开图片
            try:
                with Image.open(abs_image_path) as img:
                    # 如果图片有透明通道，转换为RGB模式
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # 创建白色背景
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 保存为PDF
                    img.save(abs_pdf_path, 'PDF', resolution=100.0)

            except Exception as img_error:
                print(f"[ERROR] 处理图片时出错: {img_error}")
                return False

            # 验证PDF是否生成
            if abs_pdf_path.exists():
                file_size = abs_pdf_path.stat().st_size
                print(f"[OK] 图片转换成功! 文件大小: {file_size} bytes")
                return True
            else:
                print("[ERROR] PDF文件生成失败")
                return False

        except Exception as e:
            print(f"[ERROR] 图片转换失败: {e}")
            return False

def find_word_files(directory, use_template=False):
    """递归查找所有Word文件，可选择使用模板筛选"""
    word_extensions = {'.doc', '.docx'}
    word_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if Path(file).suffix.lower() in word_extensions:
                word_files.append(file_path)

    return word_files

def find_image_files(directory, use_template=False):
    """递归查找所有图片文件，可选择使用模板筛选"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}
    image_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if Path(file).suffix.lower() in image_extensions:
                image_files.append(file_path)

    return image_files

def batch_convert_data_folder(gui_mode=False, confirmation_callback=None, template_path=None):
    """批量转换data文件夹中的所有Word文件
    参数:
        gui_mode: 是否为GUI模式
        confirmation_callback: GUI模式下的确认回调函数
        template_path: 模板文件路径，如果提供则使用模板筛选
    """
    data_folder = get_app_path("data")
    
    # 检查data文件夹是否存在
    if not os.path.exists(data_folder):
        print(f"[ERROR] 文件夹不存在: {data_folder}")
        return False
    
    if not os.path.isdir(data_folder):
        print(f"[ERROR] 路径不是文件夹: {data_folder}")
        return False
    
    print("[SEARCH] 正在搜索Word文件...")
    word_files = find_word_files(data_folder)

    if not word_files:
        print("[ERROR] 在data文件夹中没有找到任何Word文件")
        return True
    
    # 根据是否使用模板决定处理方式
    files_to_process = word_files  # 默认处理所有文件
    converter = None

    if template_path:
        # 使用模板模式
        print("\n" + "="*80)
        print(f"[TEMPLATE] 📋 模板模式已启用")
        print(f"[TEMPLATE] 📁 模板文件路径: {template_path}")
        print(f"[TEMPLATE] [OK] 文件是否存在: {os.path.exists(template_path) if template_path else False}")
        print("="*80 + "\n")
        
        converter = FinalWordToPDFConverter(template_path)
        
        # 检查模板是否成功加载
        if not converter.use_template or not converter.template_data:
            print("\n" + "⚠️  " + "="*76 + " ⚠️")
            print("⚠️  警告：模板文件未能正确加载！将转换所有Word文件！")
            print(f"⚠️  use_template: {converter.use_template}")
            print(f"⚠️  template_data 存在: {converter.template_data is not None}")
            print("⚠️  " + "="*76 + " ⚠️\n")
        else:
            rules_count = len(converter.template_data.get('rules', {}))
            print(f"[OK] 模板加载成功！包含 {rules_count} 条规则\n")
        
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

        # 筛选符合模板的文件
        filtered_files = []
        print(f"[FILTER] 🔍 开始根据模板筛选文件（共 {len(word_files)} 个文件）...")
        print("-"*80)
        
        for i, word_file in enumerate(word_files, 1):
            matches = converter.file_matches_template(word_file)
            if matches:
                filtered_files.append(word_file)

        print("-"*80)
        print(f"[RESULT] [OK] 筛选完成: {len(filtered_files)}/{len(word_files)} 个文件匹配模板")
        print("="*80 + "\n")

        if not filtered_files:
            print("[ERROR] 没有找到符合模板规则的Word文件")
            return True

        print(f"[INFO] 根据模板筛选后，实际处理 {len(filtered_files)} 个文件\n")
        files_to_process = filtered_files
    else:
        # 无模板模式，处理所有文件
        converter = FinalWordToPDFConverter()
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

    # 显示将要处理的文件列表
    if gui_mode and template_path:
        # GUI模式且使用模板时，只显示匹配的文件
        print(f"[STATS] 根据模板筛选后，将处理 {len(files_to_process)} 个文件:")
        for i, file_path in enumerate(files_to_process, 1):
            rel_path = os.path.relpath(file_path, data_folder)
            print(f"  {i:3d}. {rel_path}")
    else:
        # 非GUI模式或不使用模板时，显示所有文件
        print(f"[STATS] 找到 {len(word_files)} 个Word文件:")
        for i, file_path in enumerate(word_files, 1):
            rel_path = os.path.relpath(file_path, data_folder)
            print(f"  {i:3d}. {rel_path}")

    # 确认批量操作
    if not gui_mode:
        if template_path:
            print(f"\n[WARNING]  即将转换 {len(files_to_process)} 个符合模板规则的Word文件为PDF")
        else:
            print(f"\n[WARNING]  即将转换所有Word文件为PDF")
        confirm = input("确认继续批量处理吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("[ERROR] 操作已取消")
            return False
    else:
        # GUI模式下的确认
        if confirmation_callback:
            if template_path:
                message = f"找到 {len(word_files)} 个Word文件，根据模板筛选后将处理 {len(files_to_process)} 个文件：\n\n"
                for i, file_path in enumerate(files_to_process[:10], 1):  # 只显示匹配的文件，最多显示10个
                    rel_path = os.path.relpath(file_path, data_folder)
                    message += f"{i:2d}. {rel_path}\n"
                if len(files_to_process) > 10:
                    message += f"\n... 还有 {len(files_to_process) - 10} 个文件\n"
            else:
                message = f"找到 {len(word_files)} 个Word文件，即将进行批量转换：\n\n"
                for i, file_path in enumerate(word_files[:10], 1):  # 最多显示10个
                    rel_path = os.path.relpath(file_path, data_folder)
                    message += f"{i:2d}. {rel_path}\n"
                if len(word_files) > 10:
                    message += f"\n... 还有 {len(word_files) - 10} 个文件\n"

            message += "\n转换后的PDF文件将保存在原文件所在位置。\n\n是否继续？"

            if not confirmation_callback("确认批量Word转PDF", message):
                print("[ERROR] 用户取消了操作")
                return False

    # 统计信息
    total_files = len(word_files)
    converted_count = 0
    failed_count = 0
    skipped_count = 0
    
    print(f"\n[START] 开始批量转换...")
    print("=" * 80)
    
    # 显示"保留原文件"设置
    if converter:
        print(f"[CONFIG] 保留原文件设置: {'是' if converter.keep_original_files else '否（转换后将删除Word文件）'}")
        print("=" * 80)

    # 处理每个Word文件
    for i, word_file in enumerate(files_to_process, 1):
        print(f"\n[FILE] [{i}/{len(files_to_process)}] 处理文件: {os.path.basename(word_file)}")
        print(f"[DIR] 路径: {word_file}")

        try:
            # 设置PDF输出路径（与Word文件相同位置，只改扩展名）
            word_path = Path(word_file)
            pdf_file = word_path.with_suffix('.pdf')

            # 检查PDF是否已存在
            if pdf_file.exists():
                print(f"[SKIP]  PDF文件已存在，跳过: {pdf_file.name}")
                skipped_count += 1
                continue

            # 转换文件
            success = converter.convert_single_file(word_file, pdf_file)

            if success:
                converted_count += 1
                print(f"[OK] 转换成功: {pdf_file.name}")
            else:
                failed_count += 1
                print(f"[ERROR] 转换失败: {word_path.name}")

        except KeyboardInterrupt:
            print("\n[WARNING]  用户中断操作")
            break
        except Exception as e:
            failed_count += 1
            print(f"[ERROR] 处理文件时出错: {e}")

    # 显示最终统计结果
    print("\n" + "=" * 80)
    print("[STATS] 批量转换完成！统计结果:")
    print(f"  [FILE] 总文件数: {len(files_to_process)}")
    print(f"  [OK] 成功转换: {converted_count}")
    print(f"  [ERROR] 转换失败: {failed_count}")
    print(f"  [SKIP]  跳过文件: {skipped_count}")
    print(f"  [STATS] 处理完成率: {((converted_count + skipped_count) / len(files_to_process) * 100):.1f}%")

    return converted_count > 0

def batch_convert_all_data_folder(gui_mode=False, confirmation_callback=None, template_path=None):
    """批量转换data文件夹中的所有支持的文件（Word和图片）
    参数:
        gui_mode: 是否为GUI模式
        confirmation_callback: GUI模式下的确认回调函数
    """
    data_folder = get_app_path("data")

    # 检查data文件夹是否存在
    if not os.path.exists(data_folder):
        print(f"[ERROR] 文件夹不存在: {data_folder}")
        return False

    if not os.path.isdir(data_folder):
        print(f"[ERROR] 路径不是文件夹: {data_folder}")
        return False

    print("[SEARCH] 正在搜索所有支持的文件...")
    word_files = find_word_files(data_folder)
    image_files = find_image_files(data_folder)
    all_files = word_files + image_files

    if not all_files:
        print("[ERROR] 在data文件夹中没有找到任何支持的文件")
        return True

    # 按类型统计文件
    word_count = len(word_files)
    image_count = len(image_files)
    total_files = len(all_files)

    print(f"[STATS] 找到 {total_files} 个文件:")
    print(f"  [FILE] Word文件: {word_count} 个")
    print(f"  [IMAGE]  图片文件: {image_count} 个")

    # 根据是否使用模板决定处理方式
    files_to_process = all_files  # 默认处理所有文件
    converter = None

    if template_path:
        # 使用模板模式
        converter = FinalWordToPDFConverter(template_path)
        print(f"[DEBUG] 转换器创建完成，模板路径: {converter.template_path}")
        print(f"[DEBUG] 使用模板: {converter.use_template}")
        print(f"[DEBUG] 模板数据: {converter.template_data is not None}")
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

        # 筛选符合模板的文件
        filtered_files = []
        for file_path in all_files:
            if converter.file_matches_template(file_path):
                filtered_files.append(file_path)

        if not filtered_files:
            print("[ERROR] 没有找到符合模板规则的文件")
            return True

        print(f"[INFO] 根据模板筛选后，实际处理 {len(filtered_files)} 个文件")
        files_to_process = filtered_files
    else:
        # 不使用模板模式，处理所有文件
        converter = FinalWordToPDFConverter()
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

    # 显示文件列表
    for i, file_path in enumerate(files_to_process[:10], 1):  # 最多显示10个
        rel_path = os.path.relpath(file_path, data_folder)
        print(f"  {i:3d}. {rel_path}")
    if len(files_to_process) > 10:
        print(f"  ... 还有 {len(files_to_process) - 10} 个文件")

    # 确认批量操作
    if not gui_mode:
        template_info = f" (使用模板: {os.path.basename(template_path)})" if template_path else ""
        print(f"\n[WARNING]  即将转换{template_info}所有支持的文件为PDF")
        confirm = input("确认继续批量处理吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("[ERROR] 操作已取消")
            return False
    else:
        # GUI模式下的确认
        if confirmation_callback:
            template_info = f" (使用模板: {os.path.basename(template_path)})" if template_path else ""
            if template_path:
                message = f"找到 {len(all_files)} 个文件{template_info}，根据模板筛选后将处理 {len(files_to_process)} 个文件：\n\n"
            else:
                message = f"找到 {len(files_to_process)} 个文件{template_info}，即将进行批量转换：\n\n"

            message += f"[FILE] Word文件: {word_count} 个\n"
            message += f"[IMAGE]  图片文件: {image_count} 个\n\n"

            # 只显示匹配的文件（如果是使用模板的情况）
            display_files = files_to_process if template_path else files_to_process
            for i, file_path in enumerate(display_files[:10], 1):  # 最多显示10个
                rel_path = os.path.relpath(file_path, data_folder)
                message += f"{i:2d}. {rel_path}\n"
            if len(display_files) > 10:
                message += f"\n... 还有 {len(display_files) - 10} 个文件\n"
            message += "\n转换后的PDF文件将保存在原文件所在位置。\n\n是否继续？"

            if not confirmation_callback("确认批量转换所有文件", message):
                print("[ERROR] 用户取消了操作")
                return False

    # 统计信息
    converted_count = 0
    failed_count = 0
    skipped_count = 0

    print(f"\n[START] 开始批量转换...")
    print("=" * 80)

    # 处理每个文件
    for i, file_path in enumerate(files_to_process, 1):
        print(f"\n[FILE] [{i}/{len(files_to_process)}] 处理文件: {os.path.basename(file_path)}")
        print(f"[DIR] 路径: {file_path}")

        try:
            # 根据文件类型选择转换方法
            file_path_obj = Path(file_path)
            pdf_file = file_path_obj.with_suffix('.pdf')

            # 检查PDF是否已存在
            if pdf_file.exists():
                print(f"[SKIP]  PDF文件已存在，跳过: {pdf_file.name}")
                skipped_count += 1
                continue

            # 根据文件扩展名选择转换方法
            file_extension = file_path_obj.suffix.lower()

            if file_extension in {'.doc', '.docx'}:
                success = converter.convert_single_file(file_path, pdf_file)
            elif file_extension in {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}:
                success = converter.convert_image_to_pdf(file_path, pdf_file)
            else:
                print(f"[WARNING]  不支持的文件类型: {file_extension}")
                failed_count += 1
                continue

            if success:
                converted_count += 1
                print(f"[OK] 转换成功: {pdf_file.name}")
            else:
                failed_count += 1
                print(f"[ERROR] 转换失败: {file_path_obj.name}")

        except KeyboardInterrupt:
            print("\n[WARNING]  用户中断操作")
            break
        except Exception as e:
            failed_count += 1
            print(f"[ERROR] 处理文件时出错: {e}")

    # 显示最终统计结果
    print("\n" + "=" * 80)
    print("[STATS] 批量转换完成！统计结果:")
    print(f"  [FILE] 总文件数: {len(files_to_process)}")
    print(f"  [OK] 成功转换: {converted_count}")
    print(f"  [ERROR] 转换失败: {failed_count}")
    print(f"  [SKIP]  跳过文件: {skipped_count}")
    print(f"  [STATS] 处理完成率: {((converted_count + skipped_count) / len(files_to_process) * 100):.1f}%")

    return converted_count > 0

def batch_convert_images_data_folder(gui_mode=False, confirmation_callback=None, template_path=None):
    """批量转换data文件夹中的所有图片文件为PDF
    参数:
        gui_mode: 是否为GUI模式
        confirmation_callback: GUI模式下的确认回调函数
    """
    data_folder = get_app_path("data")

    # 检查data文件夹是否存在
    if not os.path.exists(data_folder):
        print(f"[ERROR] 文件夹不存在: {data_folder}")
        return False

    if not os.path.isdir(data_folder):
        print(f"[ERROR] 路径不是文件夹: {data_folder}")
        return False

    print("[SEARCH] 正在搜索图片文件...")
    image_files = find_image_files(data_folder)

    if not image_files:
        print("[ERROR] 在data文件夹中没有找到任何图片文件")
        return True

    # 根据是否使用模板决定处理方式
    files_to_process = image_files  # 默认处理所有文件
    converter = None

    if template_path:
        # 使用模板模式
        converter = FinalWordToPDFConverter(template_path)
        print(f"[DEBUG] 转换器创建完成，模板路径: {converter.template_path}")
        print(f"[DEBUG] 使用模板: {converter.use_template}")
        print(f"[DEBUG] 模板数据: {converter.template_data is not None}")
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

        # 筛选符合模板的文件
        filtered_files = []
        for image_file in image_files:
            if converter.file_matches_template(image_file):
                filtered_files.append(image_file)

        if not filtered_files:
            print("[ERROR] 没有找到符合模板规则的图片文件")
            return True

        print(f"[INFO] 根据模板筛选后，实际处理 {len(filtered_files)} 个文件")
        files_to_process = filtered_files
    else:
        # 不使用模板模式，处理所有文件
        converter = FinalWordToPDFConverter()
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

    # 显示将要处理的文件列表
    if gui_mode and template_path:
        # GUI模式且使用模板时，只显示匹配的文件
        print(f"[STATS] 根据模板筛选后，将处理 {len(files_to_process)} 个图片文件:")
        for i, file_path in enumerate(files_to_process, 1):
            rel_path = os.path.relpath(file_path, data_folder)
            print(f"  {i:3d}. {rel_path}")
    else:
        # 非GUI模式或不使用模板时，显示所有文件
        print(f"[STATS] 找到 {len(image_files)} 个图片文件:")
        for i, file_path in enumerate(image_files, 1):
            rel_path = os.path.relpath(file_path, data_folder)
            print(f"  {i:3d}. {rel_path}")

    # 确认批量操作
    if not gui_mode:
        if template_path:
            print(f"\n[WARNING]  即将转换 {len(files_to_process)} 个符合模板规则的图片文件为PDF")
        else:
            print(f"\n[WARNING]  即将转换所有图片文件为PDF")
        confirm = input("确认继续批量处理吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("[ERROR] 操作已取消")
            return False
    else:
        # GUI模式下的确认
        if confirmation_callback:
            if template_path:
                message = f"找到 {len(image_files)} 个图片文件，根据模板筛选后将处理 {len(files_to_process)} 个文件：\n\n"
            else:
                message = f"找到 {len(image_files)} 个图片文件，即将进行批量转换：\n\n"

            # 只显示匹配的文件（如果是使用模板的情况）
            display_files = files_to_process if template_path else files_to_process
            for i, file_path in enumerate(display_files[:10], 1):  # 最多显示10个
                rel_path = os.path.relpath(file_path, data_folder)
                message += f"{i:2d}. {rel_path}\n"
            if len(display_files) > 10:
                message += f"\n... 还有 {len(display_files) - 10} 个文件\n"
            message += "\n转换后的PDF文件将保存在原文件所在位置。\n\n是否继续？"

            if not confirmation_callback("确认批量图片转PDF", message):
                print("[ERROR] 用户取消了操作")
                return False

    # 统计信息
    total_files = len(image_files)
    converted_count = 0
    failed_count = 0
    skipped_count = 0

    print(f"\n[START] 开始批量转换图片...")
    print("=" * 80)

    # 根据是否使用模板决定处理方式
    files_to_process = image_files  # 默认处理所有文件
    converter = None

    if template_path:
        # 使用模板模式
        converter = FinalWordToPDFConverter(template_path)
        print(f"[DEBUG] 转换器创建完成，模板路径: {converter.template_path}")
        print(f"[DEBUG] 使用模板: {converter.use_template}")
        print(f"[DEBUG] 模板数据: {converter.template_data is not None}")
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

        # 筛选符合模板的文件
        filtered_files = []
        for image_file in image_files:
            if converter.file_matches_template(image_file):
                filtered_files.append(image_file)

        if not filtered_files:
            print("[ERROR] 没有找到符合模板规则的图片文件")
            return True

        print(f"[INFO] 根据模板筛选后，实际处理 {len(filtered_files)} 个文件")
        files_to_process = filtered_files
    else:
        # 不使用模板模式，处理所有文件
        converter = FinalWordToPDFConverter()
        if not converter.initialize_word_app():
            print("[ERROR] 无法启动Office应用程序")
            print("[TIP] 请确保已安装WPS Office或Microsoft Office")
            return False

    # 处理每个图片文件
    for i, image_file in enumerate(files_to_process, 1):
        print(f"\n[IMAGE]  [{i}/{len(files_to_process)}] 处理文件: {os.path.basename(image_file)}")
        print(f"[DIR] 路径: {image_file}")

        try:
            # 设置PDF输出路径（与图片文件相同位置，只改扩展名）
            image_path = Path(image_file)
            pdf_file = image_path.with_suffix('.pdf')

            # 检查PDF是否已存在
            if pdf_file.exists():
                print(f"[SKIP]  PDF文件已存在，跳过: {pdf_file.name}")
                skipped_count += 1
                continue

            # 转换文件
            success = converter.convert_image_to_pdf(image_file, pdf_file)

            if success:
                converted_count += 1
                print(f"[OK] 转换成功: {pdf_file.name}")
            else:
                failed_count += 1
                print(f"[ERROR] 转换失败: {image_path.name}")

        except KeyboardInterrupt:
            print("\n[WARNING]  用户中断操作")
            break
        except Exception as e:
            failed_count += 1
            print(f"[ERROR] 处理文件时出错: {e}")

    # 显示最终统计结果
    print("\n" + "=" * 80)
    print("[STATS] 批量图片转换完成！统计结果:")
    print(f"  [IMAGE]  总文件数: {len(files_to_process)}")
    print(f"  [OK] 成功转换: {converted_count}")
    print(f"  [ERROR] 转换失败: {failed_count}")
    print(f"  [SKIP]  跳过文件: {skipped_count}")
    print(f"  [STATS] 处理完成率: {((converted_count + skipped_count) / len(files_to_process) * 100):.1f}%")

    return converted_count > 0

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="WPS文档和图片转PDF转换器 - 批量版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用模式:
  1. 单文件转换:
     python final_word_to_pdf.py document.docx
     python final_word_to_pdf.py document.docx -o output.pdf
     python final_word_to_pdf.py image.jpg -o image.pdf

  2. 批量转换data文件夹:
     python final_word_to_pdf.py --batch-word    # 转换所有WPS文件
     python final_word_to_pdf.py --batch-image  # 转换所有图片文件
     python final_word_to_pdf.py --batch-all    # 转换所有支持的文件

  3. 使用模板进行选择性转换:
     python final_word_to_pdf.py --batch-word --template template/word_to_pdf_templates/医疗器械文档转换模板.json
     python final_word_to_pdf.py --batch-all --template template/word_to_pdf_templates/医疗器械文档转换模板.json
        """
    )
    parser.add_argument("input_file", nargs='?', help="输入文件路径（单文件模式）")
    parser.add_argument("-o", "--output", help="输出PDF文件路径（单文件模式可选）")
    parser.add_argument("--batch-word", action="store_true", help="批量转换data文件夹中的所有WPS文件")
    parser.add_argument("--batch-image", action="store_true", help="批量转换data文件夹中的所有图片文件")
    parser.add_argument("--batch-all", action="store_true", help="批量转换data文件夹中的所有支持的文件")
    parser.add_argument("--batch", action="store_true", help="兼容选项：等同于 --batch-word")
    parser.add_argument("--template", help="使用指定模板文件进行选择性转换")

    try:
        args = parser.parse_args()
    except SystemExit:
        return 1

    print("[START] Word转PDF转换器 - 批量版")
    print("=" * 50)

    # 批量模式
    if args.batch_all:
        template_msg = f" (使用模板: {args.template})" if args.template else ""
        print(f"[DIR] 批量转换模式: 处理data文件夹中的所有支持文件{template_msg}")
        success = batch_convert_all_data_folder(template_path=args.template)
        if success:
            print("\n[SUCCESS] 批量转换完成!")
            return 0
        else:
            print("\n[FAILED] 批量转换失败!")
            return 1

    elif args.batch_word:
        template_msg = f" (使用模板: {args.template})" if args.template else ""
        print(f"[DIR] 批量转换模式: 处理data文件夹中的所有WPS文件{template_msg}")
        success = batch_convert_data_folder(template_path=args.template)
        if success:
            print("\n[SUCCESS] 批量转换完成!")
            return 0
        else:
            print("\n[FAILED] 批量转换失败!")
            return 1

    elif args.batch_image:
        template_msg = f" (使用模板: {args.template})" if args.template else ""
        print(f"[DIR] 批量转换模式: 处理data文件夹中的所有图片文件{template_msg}")
        success = batch_convert_images_data_folder(template_path=args.template)
        if success:
            print("\n[SUCCESS] 批量转换完成!")
            return 0
        else:
            print("\n[FAILED] 批量转换失败!")
            return 1

    elif args.batch:  # 兼容旧参数
        template_msg = f" (使用模板: {args.template})" if args.template else ""
        print(f"[DIR] 批量转换模式: 处理data文件夹中的所有WPS文件（兼容模式）{template_msg}")
        success = batch_convert_data_folder(template_path=args.template)
        if success:
            print("\n[SUCCESS] 批量转换完成!")
            return 0
        else:
            print("\n[FAILED] 批量转换失败!")
            return 1

    # 单文件模式
    if not args.input_file:
        print("[ERROR] 请指定输入文件路径或使用批量转换参数")
        parser.print_help()
        return 1

    # 判断文件类型
    input_path = Path(args.input_file)
    file_extension = input_path.suffix.lower()

    if file_extension in {'.doc', '.docx'}:
        # Word文件转换
        with FinalWordToPDFConverter() as converter:
            # 初始化WPS
            if not converter.initialize_word_app():
                print("[ERROR] 无法启动Office应用程序")
                print("[TIP] 请确保已安装WPS Office或Microsoft Office")
                return 1

            # 执行转换
            success = converter.convert_single_file(args.input_file, args.output)

            if success:
                print("\n[SUCCESS] WPS转换完成!")
                return 0
            else:
                print("\n[FAILED] WPS转换失败!")
                return 1

    elif file_extension in {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}:
        # 图片文件转换
        converter = FinalWordToPDFConverter()
        success = converter.convert_image_to_pdf(args.input_file, args.output)

        if success:
            print("\n[SUCCESS] 图片转换完成!")
            return 0
        else:
            print("\n[FAILED] 图片转换失败!")
            return 1

    else:
        print(f"[ERROR] 不支持的文件类型: {file_extension}")
        print("[TIP] 支持的文件类型: .doc, .docx, .jpg, .jpeg, .png, .bmp, .gif, .tiff, .tif, .webp")
        return 1

if __name__ == "__main__":
    sys.exit(main())


