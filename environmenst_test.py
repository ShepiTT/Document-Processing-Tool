#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础环境测试模块
用于检查基本的Python环境和依赖
"""

import sys
import os
import importlib.util

def test_python_version():
    """测试Python版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 6:
        print(f"✅ Python版本: {sys.version.split()[0]}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        return False

def test_basic_modules():
    """测试基础模块"""
    basic_modules = ['os', 'sys', 'json', 'zipfile', 'pathlib']
    all_passed = True

    for module in basic_modules:
        try:
            importlib.import_module(module)
            print(f"✅ 基础模块 {module} - 可用")
        except ImportError:
            print(f"❌ 基础模块 {module} - 不可用")
            all_passed = False

    return all_passed

def test_optional_modules():
    """测试可选模块"""
    optional_modules = {
        'tkinter': 'GUI界面',
        'PIL': '图像处理',
        'fitz': 'PDF处理(PyMuPDF)',
        'pytesseract': 'OCR识别'
    }

    all_passed = True
    for module, description in optional_modules.items():
        try:
            importlib.import_module(module)
            print(f"✅ 可选模块 {module} ({description}) - 可用")
        except ImportError:
            print(f"⚠️  可选模块 {module} ({description}) - 不可用")
            # 可选模块不影响整体结果

    return all_passed

def test_directory_structure():
    """测试目录结构"""
    required_dirs = ['data', 'output', 'template/rename_templates', 'template/folder_templates']
    all_passed = True

    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ 目录 {directory} - 存在")
        else:
            print(f"⚠️  目录 {directory} - 不存在")
            # 这些目录可能需要创建，不算错误

    return all_passed

def run_full_test():
    """
    运行完整的基础环境测试

    Returns:
        bool: 测试是否全部通过
    """
    print("=" * 50)
    print("🚀 开始基础环境测试")
    print("=" * 50)

    tests = [
        test_python_version,
        test_basic_modules,
        test_optional_modules,
        test_directory_structure
    ]

    results = []
    for test_func in tests:
        print(f"\n📋 正在执行: {test_func.__name__}")
        print("-" * 30)
        result = test_func()
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)

    passed_count = sum(results)
    total_count = len(results)

    if passed_count == total_count:
        print("🎉 所有基础环境测试通过！")
        print("✅ 系统环境正常，可以使用相关功能")
        return True
    else:
        print(f"⚠️  有 {total_count - passed_count} 项测试未通过")
        print("💡 某些功能可能受到影响，建议检查相关依赖")
        return False

if __name__ == "__main__":
    run_full_test()
