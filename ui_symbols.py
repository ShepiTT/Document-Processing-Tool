#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI符号配置
统一管理界面显示的符号，支持emoji和文本符号切换

作者：Lxx
"""

# 是否使用emoji（Windows Tkinter不支持彩色emoji，建议设为False）
USE_EMOJI = False

if USE_EMOJI:
    # Emoji 符号
    SYMBOLS = {
        'package': '📦',
        'folder': '📁',
        'file': '📄',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'search': '🔍',
        'rocket': '🚀',
        'chart': '📊',
        'target': '🎯',
        'memo': '📝',
        'skip': '⏭️',
        'arrow_right': '→',
        'arrow_down': '↓',
        'check': '✓',
        'cross': '✗',
        'bullet': '•',
        'tag': '[Tag]',
        'clean': '[Clean]',
        'word': '[File]',
    }
else:
    # 文本符号（兼容性更好）
    SYMBOLS = {
        'package': '[包]',
        'folder': '[夹]',
        'file': '[文]',
        'success': '[√]',
        'error': '[×]',
        'warning': '[!]',
        'info': '[i]',
        'search': '[搜]',
        'rocket': '[>]',
        'chart': '[图]',
        'target': '[*]',
        'memo': '[记]',
        'skip': '[跳]',
        'arrow_right': '->',
        'arrow_down': '|',
        'check': '√',
        'cross': '×',
        'bullet': '·',
        'tag': '[Tag]',
        'clean': '[Clean]',
        'word': '[File]',
    }


def get_symbol(key):
    """获取符号"""
    return SYMBOLS.get(key, '')


# 便捷访问
package = SYMBOLS['package']
folder = SYMBOLS['folder']
file = SYMBOLS['file']
success = SYMBOLS['success']
error = SYMBOLS['error']
warning = SYMBOLS['warning']
info = SYMBOLS['info']
search = SYMBOLS['search']
rocket = SYMBOLS['rocket']
chart = SYMBOLS['chart']
target = SYMBOLS['target']
memo = SYMBOLS['memo']
skip = SYMBOLS['skip']
arrow_right = SYMBOLS['arrow_right']
arrow_down = SYMBOLS['arrow_down']
check = SYMBOLS['check']
cross = SYMBOLS['cross']
bullet = SYMBOLS['bullet']
