#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyMuPDF安装检测脚本
用于诊断PDF合并功能的依赖问题

作者：Lxx   
更新时间：2025-09-25
"""

import sys
import os

def check_pymupdf():
    """检查PyMuPDF安装状态"""
    print("🔍 PyMuPDF依赖检测")
    print("=" * 40)
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print()
    
    # 尝试导入fitz
    try:
        import fitz
        print("✅ 成功导入 fitz 模块")
        print(f"✅ PyMuPDF版本: {fitz.VersionBind}")
        print(f"✅ fitz模块路径: {fitz.__file__}")
        
        # 测试基本功能
        try:
            # 创建一个空的PDF文档进行测试
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), "Test")
            doc.close()
            print("✅ PyMuPDF基本功能测试通过")
            
        except Exception as e:
            print(f"❌ PyMuPDF功能测试失败: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ 无法导入 fitz 模块: {e}")
        print("\n💡 解决方案:")
        print("   1. 安装PyMuPDF: pip install PyMuPDF")
        print("   2. 或者安装指定版本: pip install PyMuPDF==1.23.4")
        print("   3. 检查是否有多个Python环境")
        return False
    except Exception as e:
        print(f"❌ 导入 fitz 模块时发生错误: {e}")
        return False
    
    # 检查其他相关模块
    print("\n🔍 检查其他依赖模块:")
    modules_to_check = [
        'tkinter',
        'pathlib', 
        'threading',
        'queue'
    ]
    
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except ImportError:
            print(f"❌ {module_name}")
    
    print("\n✅ PyMuPDF依赖检测完成!")
    return True

def check_pdf_merger():
    """检查PDF合并器模块"""
    print("\n🔍 PDF合并器模块检测")
    print("=" * 40)
    
    try:
        from pdf_merger import PDFMerger
        print("✅ 成功导入 PDFMerger 类")
        
        merger = PDFMerger()
        if merger.supported:
            print("✅ PDF合并器初始化成功")
            print("✅ PDF合并功能可用")
        else:
            print("❌ PDF合并器不支持")
            print("💡 这通常表示PyMuPDF未正确安装")
            return False
            
    except ImportError as e:
        print(f"❌ 无法导入 PDFMerger: {e}")
        print("💡 请确保 pdf_merger.py 文件存在")
        return False
    except Exception as e:
        print(f"❌ PDF合并器检测出错: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🏥 医疗器械文档处理工具 - PDF功能诊断")
    print("=" * 50)
    
    # 检查PyMuPDF
    pymupdf_ok = check_pymupdf()
    
    # 检查PDF合并器
    merger_ok = check_pdf_merger()
    
    print("\n" + "=" * 50)
    print("📋 诊断结果:")
    
    if pymupdf_ok and merger_ok:
        print("✅ 所有检测通过，PDF合并功能应该可以正常使用")
    else:
        print("❌ 检测到问题，PDF合并功能可能无法正常使用")
        print("\n💡 建议:")
        if not pymupdf_ok:
            print("   • 重新安装PyMuPDF: pip uninstall PyMuPDF && pip install PyMuPDF")
        if not merger_ok:
            print("   • 检查pdf_merger.py文件是否存在")
            print("   • 如果是exe版本，可能需要重新构建")
    
    print("\n按回车键退出...")
    input()

if __name__ == "__main__":
    main()