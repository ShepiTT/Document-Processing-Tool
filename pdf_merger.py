#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF处理工具
支持PDF合并等功能

作者：Lxx
更新时间：2025-10-13
"""

import os
import sys
import json
from pathlib import Path
import traceback

try:
    import fitz  # PyMuPDF
    PyMuPDF = fitz
    print(f"[OK] PyMuPDF已成功加载，版本: {fitz.VersionBind}")
except ImportError as e:
    PyMuPDF = None
    fitz = None
    print(f"[ERROR] PyMuPDF导入失败: {e}")
    print("请检查PyMuPDF安装: pip install PyMuPDF")
except Exception as e:
    PyMuPDF = None
    fitz = None
    print(f"[ERROR] PyMuPDF加载异常: {e}")

class PDFProcessor:
    """PDF处理工具类"""

    def __init__(self, template_file=None):
        self.supported = PyMuPDF is not None
        self.template_file = template_file
        self.template_data = None
        self.template_name = ""

        if not self.supported:
            print("[WARNING] PDF处理功能需要安装PyMuPDF库")
            print("请运行: pip install PyMuPDF")

        if template_file:
            self.load_template()

    def load_template(self):
        """加载重命名模板文件"""
        if not self.template_file or not os.path.exists(self.template_file):
            return False

        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                self.template_data = json.load(f)

            self.template_name = self.template_data.get('name', Path(self.template_file).stem)
            print(f"已加载模板: {self.template_name}")
            return True

        except Exception as e:
            print(f"加载模板失败 {self.template_file}: {e}")
            return False

    def scan_directory_for_pdfs(self, directory, progress_callback=None):
        """扫描目录中的PDF文件"""
        if not os.path.exists(directory):
            if progress_callback:
                progress_callback(f"❌ 目录不存在: {directory}")
            return []

        pdf_files = []
        for file_path in Path(directory).rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                pdf_info = self.get_pdf_info(str(file_path), directory)
                if pdf_info:
                    pdf_files.append(pdf_info)

        if progress_callback:
            progress_callback(f"📄 找到 {len(pdf_files)} 个PDF文件")

        return pdf_files

    def merge_pdfs(self, pdf_files, output_path, progress_callback=None):
        """
        合并PDF文件
        
        Args:
            pdf_files (list): PDF文件路径列表
            output_path (str): 输出文件路径
            progress_callback (function): 进度回调函数
            
        Returns:
            bool: 合并是否成功
        """
        if not self.supported or fitz is None:
            if progress_callback:
                progress_callback("❌ PDF合并功能不可用，请安装PyMuPDF库")
            return False
        
        if not pdf_files:
            if progress_callback:
                progress_callback("❌ 没有选择PDF文件")
            return False
        
        try:
            # 创建输出目录
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建新的PDF文档
            merged_doc = fitz.open()
            
            total_files = len(pdf_files)
            total_pages = 0
            
            for i, pdf_file in enumerate(pdf_files, 1):
                if progress_callback:
                    progress_callback(f"📄 正在处理文件 {i}/{total_files}: {Path(pdf_file).name}")
                
                try:
                    # 检查文件是否存在
                    if not os.path.exists(pdf_file):
                        if progress_callback:
                            progress_callback(f"⚠️ 文件不存在，跳过: {Path(pdf_file).name}")
                        continue
                    
                    # 打开PDF文件
                    doc = fitz.open(pdf_file)
                    
                    if doc.page_count == 0:
                        if progress_callback:
                            progress_callback(f"⚠️ 文件无页面，跳过: {Path(pdf_file).name}")
                        doc.close()
                        continue
                    
                    # 将所有页面插入到合并文档中
                    merged_doc.insert_pdf(doc)
                    total_pages += doc.page_count
                    
                    if progress_callback:
                        progress_callback(f"✅ 已添加 {doc.page_count} 页 - {Path(pdf_file).name}")
                    
                    doc.close()
                    
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"❌ 处理文件出错: {Path(pdf_file).name} - {str(e)}")
                    continue
            
            if merged_doc.page_count == 0:
                merged_doc.close()
                if progress_callback:
                    progress_callback("❌ 没有成功处理任何PDF文件")
                return False
            
            # 保存合并后的PDF
            merged_doc.save(output_path)
            merged_doc.close()
            
            if progress_callback:
                progress_callback(f"🎉 PDF合并完成！")
                progress_callback(f"📊 合并统计:")
                progress_callback(f"  • 处理文件: {total_files} 个")
                progress_callback(f"  • 总页数: {total_pages} 页")
                progress_callback(f"  • 输出文件: {output_path}")
                progress_callback(f"  • 文件大小: {self._format_file_size(os.path.getsize(output_path))}")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ PDF合并失败: {str(e)}")
                progress_callback(f"详细错误: {traceback.format_exc()}")
            return False
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def validate_pdf_files(self, pdf_files, progress_callback=None):
        """
        验证PDF文件列表
        
        Args:
            pdf_files (list): PDF文件路径列表
            progress_callback (function): 进度回调函数
            
        Returns:
            list: 有效的PDF文件列表
        """
        if not self.supported or fitz is None:
            return []
        
        valid_files = []
        
        for pdf_file in pdf_files:
            try:
                if not os.path.exists(pdf_file):
                    if progress_callback:
                        progress_callback(f"⚠️ 文件不存在: {Path(pdf_file).name}")
                    continue
                
                if not pdf_file.lower().endswith('.pdf'):
                    if progress_callback:
                        progress_callback(f"⚠️ 不是PDF文件: {Path(pdf_file).name}")
                    continue
                
                # 尝试打开PDF文件验证
                try:
                    doc = fitz.open(pdf_file)
                    page_count = doc.page_count
                    doc.close()
                    
                    if page_count > 0:
                        valid_files.append(pdf_file)
                        if progress_callback:
                            progress_callback(f"✅ 有效PDF文件: {Path(pdf_file).name} ({page_count} 页)")
                    else:
                        if progress_callback:
                            progress_callback(f"⚠️ PDF文件无页面: {Path(pdf_file).name}")
                
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"❌ PDF文件损坏: {Path(pdf_file).name} - {str(e)}")
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ 验证文件出错: {Path(pdf_file).name} - {str(e)}")
        
        return valid_files
    
    def get_pdf_info(self, pdf_file, target_dir=None):
        """
        获取PDF文件信息

        Args:
            pdf_file (str): PDF文件路径
            target_dir (str): 目标目录，用于计算相对路径

        Returns:
            dict: PDF信息字典
        """
        if not self.supported or fitz is None:
            return None

        try:
            doc = fitz.open(pdf_file)
            info = {
                'file_name': Path(pdf_file).name,
                'file_path': pdf_file,
                'page_count': doc.page_count,
                'file_size': os.path.getsize(pdf_file),
                'file_size_formatted': self._format_file_size(os.path.getsize(pdf_file)),
                'title': doc.metadata.get('title', '') if doc.metadata else '',
                'author': doc.metadata.get('author', '') if doc.metadata else '',
                'subject': doc.metadata.get('subject', '') if doc.metadata else '',
                'creator': doc.metadata.get('creator', '') if doc.metadata else '',
            }

            # 添加相对路径
            if target_dir:
                try:
                    info['relative_path'] = str(Path(pdf_file).relative_to(target_dir))
                except ValueError:
                    # 如果文件不在目标目录内，使用完整路径
                    info['relative_path'] = pdf_file
            else:
                info['relative_path'] = pdf_file

            doc.close()
            return info
        except Exception as e:
            return {
                'file_name': Path(pdf_file).name,
                'file_path': pdf_file,
                'relative_path': pdf_file if not target_dir else str(Path(pdf_file).relative_to(target_dir)) if Path(pdf_file).is_relative_to(target_dir) else pdf_file,
                'error': str(e)
            }

def main():
    """主函数 - 用于测试"""
    processor = PDFProcessor()

    if not processor.supported:
        print("PDF处理功能不可用")
        return

    # 示例用法
    print("PDF处理工具测试")
    print("请手动修改template_file和target_dir参数进行测试")

    # 测试参数（请修改为实际文件路径）
    template_file = "template/rename_templates/牙科手机模板.json"
    target_dir = "data/0010600120240123"

    def print_progress(message):
        print(message)

    # 加载模板
    if processor.load_template():
        print("模板加载成功")
        print(f"模板名称: {processor.template_name}")
    else:
        print("模板加载失败")

if __name__ == "__main__":
    main()