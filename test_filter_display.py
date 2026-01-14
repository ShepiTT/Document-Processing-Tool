#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Word转PDF筛选显示功能
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.getcwd())

def test_filter_display():
    """测试筛选显示功能"""
    print("[TEST] 开始测试筛选显示功能...")

    try:
        from final_word_to_pdf import batch_convert_data_folder

        # 模拟GUI模式调用，带模板
        print("\n[TEST] 模拟GUI模式调用（带模板）...")

        # 重定向print输出以捕获内容
        import io
        from contextlib import redirect_stdout

        # 创建一个假的确认回调函数，总是返回True
        def fake_confirmation(title, message):
            print(f"[FAKE GUI CONFIRM] {title}")
            print("Message preview:", message[:200] + "..." if len(message) > 200 else message)
            return True

        # 捕获输出
        f = io.StringIO()
        with redirect_stdout(f):
            result = batch_convert_data_folder(
                gui_mode=True,
                confirmation_callback=fake_confirmation,
                template_path="template/word_to_pdf_templates/医疗器械文档转换1.json"
            )

        output = f.getvalue()
        print(f"[RESULT] 函数返回: {result}")
        print("\n[CAPTURED OUTPUT]")
        print("=" * 60)
        print(output[:1000])  # 只显示前1000个字符
        print("..." if len(output) > 1000 else "")
        print("=" * 60)

        # 检查输出中是否包含筛选信息
        if "根据模板筛选后" in output:
            print("[OK] ✅ 找到了筛选信息")
        else:
            print("[ERROR] ❌ 未找到筛选信息")

        if "匹配的文件" in output or "将被转换" in output:
            print("[OK] ✅ 显示了匹配的文件信息")
        else:
            print("[ERROR] ❌ 未显示匹配的文件信息")

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_filter_display()
