#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZIP文件批量解压工具（自动修复中文文件名乱码）
------------------------------------------------
功能：
1. 递归扫描 data/ 文件夹下的所有 ZIP 文件
2. 自动识别并正确解码文件名编码（UTF-8 / GBK）
3. 每个 ZIP 文件解压到以文件名命名的子文件夹中
4. 输出日志与统计信息

作者：Lxx
更新时间：2025-10-15
"""

import os
import zipfile
import shutil
from pathlib import Path


# ====================================================
# ✅ 解压单个 ZIP 文件（含中文文件名自动识别）
# ====================================================
def unzip_fix_encoding(zip_path, extract_to):
    """
    解压单个 ZIP 文件，自动修复文件名乱码
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for info in zf.infolist():
            try:
                # 1. 处理编码问题
                if info.flag_bits & 0x800:
                    # 如果设置了 bit 11，说明文件名已经是 UTF-8 编码，zipfile 已自动正确解码
                    name = info.filename
                else:
                    # 否则，尝试将 zipfile 默认按 cp437 解码的结果还原回字节流，再重新按 GBK 解码（Windows 常见）
                    try:
                        name = info.filename.encode('cp437').decode('gbk')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        try:
                            # 尝试 UTF-8
                            name = info.filename.encode('cp437').decode('utf-8')
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            # 如果都失败，则保留原样
                            name = info.filename

                target_path = os.path.join(extract_to, name)

                # ✅ 判断是否是目录
                if info.is_dir():
                    os.makedirs(target_path, exist_ok=True)
                    continue

                # 确保上层目录存在
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # 写出文件
                with open(target_path, "wb") as f:
                    f.write(zf.read(info))
            except Exception as e:
                # 单个文件解压失败不影响后续，但打印日志
                print(f"  ⚠️ 警告: 无法解压文件 {info.filename}: {e}")


# ====================================================
# ✅ 主逻辑：递归解压 data/ 目录下的所有 ZIP 文件
# ====================================================
def unzip_files_in_data_folder():
    """
    遍历 data/ 文件夹下所有 ZIP 文件并批量解压
    """
    data_dir = Path("data")

    if not data_dir.exists():
        print("❌ data 文件夹不存在！")
        return False

    total_zips = 0
    success_zips = 0
    failed_zips = []

    print("🚀 开始批量解压 ZIP 文件...\n")

    for zip_path in data_dir.rglob("*.zip"):
        total_zips += 1
        print(f"📦 处理: {zip_path}")

        try:
            # 解压到同名文件夹（去掉扩展名）
            extract_dir = zip_path.parent / zip_path.stem

            # 若文件夹存在则清空
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir, exist_ok=True)

            # 调用解压函数
            unzip_fix_encoding(str(zip_path), str(extract_dir))

            print(f"  ✅ 解压完成: {extract_dir}")
            success_zips += 1

        except zipfile.BadZipFile:
            print("  ❌ 错误: 文件不是有效的 ZIP 压缩包")
            failed_zips.append((zip_path, "Bad ZIP file"))
        except PermissionError as e:
            print(f"  ❌ 权限错误: {e}")
            failed_zips.append((zip_path, "Permission denied"))
        except Exception as e:
            print(f"  ❌ 解压失败: {e}")
            failed_zips.append((zip_path, str(e)))

    # 打印统计结果
    print("\n📊 解压统计")
    print(f"   总计: {total_zips}")
    print(f"   成功: {success_zips}")
    print(f"   失败: {len(failed_zips)}")

    if failed_zips:
        print("\n❌ 失败详情:")
        for f, reason in failed_zips:
            print(f"   - {f}: {reason}")

    return success_zips == total_zips


# ====================================================
# ✅ 入口
# ====================================================
if __name__ == "__main__":
    unzip_files_in_data_folder()
