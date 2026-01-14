#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗器械模板验证器 - 增强版
用于验证和识别五种医疗器械申报模板类型
模板类型：
  1. 文件夹模板 (folder_templates) - 定义文件夹结构
  2. 重命名模板 (rename_templates) - 定义文件重命名规则
  3. 数据读取模板 (data_read_templates) - 定义数据读取规则
  4. 清理配置模板 (clean_templates) - 定义文件清理规则
  5. 文档转换模板 (word_to_pdf_templates) - 定义Word转PDF规则

作者：AI助手
更新时间：2025-01-20
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from enum import Enum

class TemplateType(Enum):
    """模板类型枚举"""
    FOLDER = "folder_templates"          # 文件夹结构模板
    RENAME = "rename_templates"          # 重命名规则模板
    DATA_READ = "data_read_templates"    # 数据读取模板
    CLEAN = "clean_templates"            # 清理配置模板
    WORD_TO_PDF = "word_to_pdf_templates"  # 文档转换模板

class TemplateValidator:
    """医疗器械模板验证器"""

    # 必需字段（所有模板通用）
    REQUIRED_FIELDS = {
        'name',           # 模板名称
        'description',    # 模板描述
        'version',        # 版本号
        'created_date',   # 创建日期
        'author',         # 作者
    }

    # 特定模板类型的必需字段
    TEMPLATE_SPECIFIC_REQUIRED = {
        TemplateType.FOLDER: {'rules'},
        TemplateType.RENAME: {'rules'},
        TemplateType.DATA_READ: {'rules'},
        TemplateType.CLEAN: {'exclude_patterns'},
        TemplateType.WORD_TO_PDF: {'conversion_rules'},
    }

    # 可选但推荐的字段
    OPTIONAL_FIELDS = {
        'keywords',              # 通用关键词（可选）
        'folder_structure',      # 文件夹结构（可选）
        'documentation',         # 文档链接（可选）
        'supported_extensions',  # 支持的文件扩展名（可选）
        'exclude_patterns',      # 排除模式（可选）
        'conversion_rules',      # 转换规则（可选）
    }

    # 有效文件扩展名
    VALID_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png',
        '.bmp', '.gif', '.tiff', '.tif', '.webp', '.xlsx', '.xls', '.pptx'
    }

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.validation_results = {}
        self.detected_template_type = None

    def detect_template_type(self, template_data: Dict) -> Optional[TemplateType]:
        """
        自动检测模板类型

        Args:
            template_data: 模板数据字典

        Returns:
            TemplateType: 检测到的模板类型，如果无法确定则返回None
        """
        # 检查文件夹模板的特征
        if 'rules' in template_data and isinstance(template_data['rules'], dict):
            rules = template_data['rules']
            # 文件夹模板：规则值为列表
            if rules and all(isinstance(v, list) for v in rules.values() if isinstance(v, (list, dict))):
                first_val = next(iter(rules.values()))
                if isinstance(first_val, list):
                    return TemplateType.FOLDER
            # 重命名模板：规则值包含keywords、folders、tag等
            if rules and any('keywords' in v for v in rules.values() if isinstance(v, dict)):
                return TemplateType.RENAME

        # 检查数据读取模板的特征
        if 'rules' in template_data and isinstance(template_data['rules'], list):
            return TemplateType.DATA_READ

        # 检查清理配置模板的特征
        if 'exclude_patterns' in template_data:
            return TemplateType.CLEAN

        # 检查Word转PDF模板的特征
        if 'conversion_rules' in template_data:
            return TemplateType.WORD_TO_PDF

        return None

    def validate_template(self, template_path: str) -> Dict[str, Any]:
        """
        验证模板文件

        Args:
            template_path: 模板文件路径

        Returns:
            Dict: 验证结果，包含错误、警告和详细信息
        """
        self.errors = []
        self.warnings = []
        self.validation_results = {}
        self.detected_template_type = None

        # 检查文件是否存在
        if not os.path.exists(template_path):
            self.errors.append(f"模板文件不存在: {template_path}")
            return self._get_result()

        # 检查文件扩展名
        if not template_path.lower().endswith('.json'):
            self.errors.append(f"模板文件必须是JSON格式: {template_path}")
            return self._get_result()

        try:
            # 读取并解析JSON
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    self.errors.append("模板文件为空")
                    return self._get_result()

                template_data = json.loads(content)

            # 自动检测模板类型
            self.detected_template_type = self.detect_template_type(template_data)

            # 执行各种验证
            self._validate_basic_structure(template_data)
            self._validate_required_fields(template_data)
            self._validate_field_types(template_data)
            self._validate_template_specific(template_data)

            if self.detected_template_type:
                self._validate_by_template_type(template_data)

        except json.JSONDecodeError as e:
            self.errors.append(f"JSON格式错误: {str(e)}")
        except UnicodeDecodeError as e:
            self.errors.append(f"文件编码错误，请使用UTF-8编码: {str(e)}")
        except Exception as e:
            self.errors.append(f"验证过程中发生未知错误: {str(e)}")

        return self._get_result()

    def _validate_basic_structure(self, data: Dict) -> None:
        """验证基本结构"""
        if not isinstance(data, dict):
            self.errors.append("模板必须是JSON对象（字典）类型")
            return

        # 检查是否包含必需字段
        missing_fields = self.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            self.errors.append(f"缺少必需字段: {', '.join(missing_fields)}")

    def _validate_required_fields(self, data: Dict) -> None:
        """验证必需字段的存在和有效性"""
        # 验证name字段
        if 'name' in data:
            name = data['name']
            if not isinstance(name, str) or not name.strip():
                self.errors.append("'name'字段必须是非空字符串")
            elif len(name) > 100:
                self.warnings.append("'name'字段过长，建议控制在100字符以内")

        # 验证description字段
        if 'description' in data:
            desc = data['description']
            if not isinstance(desc, str) or not desc.strip():
                self.errors.append("'description'字段必须是非空字符串")
            elif len(desc) > 500:
                self.warnings.append("'description'字段过长，建议控制在500字符以内")

        # 验证version字段
        if 'version' in data:
            version = data['version']
            if not isinstance(version, str):
                self.errors.append("'version'字段必须是字符串")
            elif not re.match(r'^\d+\.\d+(\.\d+)?$', version):
                self.warnings.append("'version'字段建议使用语义化版本格式，如: 1.0.0")

        # 验证created_date字段
        if 'created_date' in data:
            date = data['created_date']
            if not isinstance(date, str):
                self.errors.append("'created_date'字段必须是字符串")
            elif not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                self.warnings.append("'created_date'字段建议使用YYYY-MM-DD格式")

        # 验证author字段
        if 'author' in data:
            author = data['author']
            if not isinstance(author, str) or not author.strip():
                self.errors.append("'author'字段必须是非空字符串")

    def _validate_field_types(self, data: Dict) -> None:
        """验证字段类型"""
        # 验证supported_extensions（如果存在）
        if 'supported_extensions' in data:
            extensions = data['supported_extensions']
            if not isinstance(extensions, list):
                self.errors.append("'supported_extensions'必须是数组")
            else:
                for ext in extensions:
                    if not isinstance(ext, str):
                        self.errors.append(f"扩展名必须是字符串: {ext}")
                    elif not ext.startswith('.'):
                        self.errors.append(f"扩展名必须以点开头: {ext}")

        # 验证keywords（如果存在）
        if 'keywords' in data:
            keywords = data['keywords']
            if not isinstance(keywords, list):
                self.errors.append("'keywords'必须是数组")

        # 验证documentation链接（如果存在）
        if 'documentation' in data:
            doc = data['documentation']
            if not isinstance(doc, str):
                self.errors.append("'documentation'必须是字符串")

    def _validate_template_specific(self, data: Dict) -> None:
        """验证模板特定字段"""
        # 检查特定模板类型的必需字段
        if self.detected_template_type:
            required = self.TEMPLATE_SPECIFIC_REQUIRED.get(self.detected_template_type, set())
            missing = required - set(data.keys())
            if missing:
                self.errors.append(f"缺少{self.detected_template_type.value}模板必需字段: {', '.join(missing)}")

    def _validate_by_template_type(self, data: Dict) -> None:
        """根据模板类型进行特定验证"""
        if self.detected_template_type == TemplateType.FOLDER:
            self._validate_folder_template(data)
        elif self.detected_template_type == TemplateType.RENAME:
            self._validate_rename_template(data)
        elif self.detected_template_type == TemplateType.DATA_READ:
            self._validate_data_read_template(data)
        elif self.detected_template_type == TemplateType.CLEAN:
            self._validate_clean_template(data)
        elif self.detected_template_type == TemplateType.WORD_TO_PDF:
            self._validate_word_to_pdf_template(data)

    def _validate_folder_template(self, data: Dict) -> None:
        """验证文件夹模板"""
        if 'rules' not in data:
            return

        rules = data['rules']
        if not isinstance(rules, dict):
            self.errors.append("文件夹模板的'rules'必须是对象类型")
            return

        if not rules:
            self.warnings.append("文件夹模板'rules'为空")
            return

        for rule_name, rule_value in rules.items():
            if not isinstance(rule_value, list):
                self.errors.append(f"文件夹规则 '{rule_name}' 的值必须是数组: {type(rule_value)}")
            elif len(rule_value) == 0:
                self.warnings.append(f"文件夹规则 '{rule_name}' 的值为空列表")
            else:
                for folder in rule_value:
                    if not isinstance(folder, str):
                        self.errors.append(f"文件夹规则 '{rule_name}' 中包含非字符串值: {folder}")

    def _validate_rename_template(self, data: Dict) -> None:
        """验证重命名模板"""
        if 'rules' not in data:
            return

        rules = data['rules']
        if not isinstance(rules, dict):
            self.errors.append("重命名模板的'rules'必须是对象类型")
            return

        if not rules:
            self.warnings.append("重命名模板'rules'为空")
            return

        for rule_name, rule_config in rules.items():
            if not isinstance(rule_config, dict):
                self.errors.append(f"重命名规则 '{rule_name}' 必须是对象类型")
                continue

            # 验证必需字段
            if 'keywords' not in rule_config and 'folders' not in rule_config:
                self.errors.append(f"重命名规则 '{rule_name}' 必须至少包含 'keywords' 或 'folders' 字段")

            # 验证keywords
            if 'keywords' in rule_config:
                keywords = rule_config['keywords']
                if not isinstance(keywords, list):
                    self.errors.append(f"规则 '{rule_name}' 的 'keywords' 必须是数组")
                elif len(keywords) == 0:
                    self.warnings.append(f"规则 '{rule_name}' 的 'keywords' 为空")
                else:
                    for keyword in keywords:
                        if not isinstance(keyword, str):
                            self.errors.append(f"规则 '{rule_name}' 的关键词必须是字符串: {keyword}")

            # 验证folders
            if 'folders' in rule_config:
                folders = rule_config['folders']
                if not isinstance(folders, list):
                    self.errors.append(f"规则 '{rule_name}' 的 'folders' 必须是数组")
                elif len(folders) == 0:
                    self.warnings.append(f"规则 '{rule_name}' 的 'folders' 为空")

            # 验证tag
            if 'tag' in rule_config:
                tag = rule_config['tag']
                if not isinstance(tag, str):
                    self.errors.append(f"规则 '{rule_name}' 的 'tag' 必须是字符串")

    def _validate_data_read_template(self, data: Dict) -> None:
        """验证数据读取模板"""
        if 'rules' not in data:
            return

        rules = data['rules']
        if not isinstance(rules, list):
            self.errors.append("数据读取模板的'rules'必须是数组类型")
            return

        if not rules:
            self.warnings.append("数据读取模板'rules'为空")
            return

        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                self.errors.append(f"数据读取规则[{idx}]必须是对象类型")
                continue

            # 验证pattern
            if 'pattern' not in rule:
                self.errors.append(f"数据读取规则[{idx}]缺少'pattern'字段")
            elif not isinstance(rule['pattern'], str):
                self.errors.append(f"数据读取规则[{idx}]的'pattern'必须是字符串")

            # 验证type
            if 'type' not in rule:
                self.errors.append(f"数据读取规则[{idx}]缺少'type'字段")
            elif rule['type'] not in ['folder', 'file', 'pattern']:
                self.warnings.append(f"数据读取规则[{idx}]的'type'为非标准值: {rule['type']}")

    def _validate_clean_template(self, data: Dict) -> None:
        """验证清理配置模板"""
        if 'exclude_patterns' in data:
            patterns = data['exclude_patterns']
            if not isinstance(patterns, list):
                self.errors.append("'exclude_patterns'必须是数组类型")
            elif len(patterns) == 0:
                self.warnings.append("'exclude_patterns'为空，清理配置可能无效")
            else:
                for idx, pattern in enumerate(patterns):
                    if not isinstance(pattern, str):
                        self.errors.append(f"排除模式[{idx}]必须是字符串")

    def _validate_word_to_pdf_template(self, data: Dict) -> None:
        """验证Word转PDF模板"""
        if 'conversion_rules' in data:
            rules = data['conversion_rules']
            if not isinstance(rules, dict):
                self.errors.append("'conversion_rules'必须是对象类型")
                return

            if not rules:
                self.warnings.append("'conversion_rules'为空")
                return

            for rule_name, rule_config in rules.items():
                if not isinstance(rule_config, dict):
                    self.errors.append(f"转换规则 '{rule_name}' 必须是对象类型")
                else:
                    # 验证source_format
                    if 'source_format' in rule_config:
                        if rule_config['source_format'] not in ['.doc', '.docx']:
                            self.warnings.append(f"规则 '{rule_name}' 的'source_format'为: {rule_config['source_format']}")

                    # 验证target_format
                    if 'target_format' in rule_config:
                        if rule_config['target_format'] != '.pdf':
                            self.warnings.append(f"规则 '{rule_name}' 的'target_format'应为.pdf，实际为: {rule_config['target_format']}")

    def _get_result(self) -> Dict[str, Any]:
        """获取验证结果"""
        result = {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }

        if self.detected_template_type:
            result['template_type'] = self.detected_template_type.value
            result['template_type_name'] = self._get_template_type_name(self.detected_template_type)
        else:
            result['template_type'] = '未识别'
            result['template_type_name'] = '无法识别的模板类型'

        return result

    @staticmethod
    def _get_template_type_name(template_type: TemplateType) -> str:
        """获取模板类型的中文名称"""
        type_names = {
            TemplateType.FOLDER: '文件夹模板',
            TemplateType.RENAME: '重命名模板',
            TemplateType.DATA_READ: '数据读取模板',
            TemplateType.CLEAN: '清理配置模板',
            TemplateType.WORD_TO_PDF: '文档转换模板',
        }
        return type_names.get(template_type, '未知类型')

    def format_validation_report(self, result: Dict[str, Any]) -> str:
        """格式化验证报告"""
        report_lines = []

        # 添加标题
        report_lines.append("=" * 60)
        report_lines.append("医疗器械模板验证报告")
        report_lines.append("=" * 60)

        # 模板类型信息
        report_lines.append(f"\n📋 模板类型识别:")
        report_lines.append(f"  • 模板类型: {result['template_type_name']} ({result['template_type']})")

        # 验证结果
        if result['is_valid']:
            report_lines.append("\n✅ 验证状态: 通过")
        else:
            report_lines.append("\n❌ 验证状态: 失败")

        # 错误信息
        if result['errors']:
            report_lines.append("\n🚨 错误信息:")
            for error in result['errors']:
                report_lines.append(f"  • {error}")

        # 警告信息
        if result['warnings']:
            report_lines.append("\n⚠️  警告信息:")
            for warning in result['warnings']:
                report_lines.append(f"  • {warning}")

        # 统计信息
        report_lines.append(f"\n📊 验证统计:")
        report_lines.append(f"  • 错误数量: {result['error_count']}")
        report_lines.append(f"  • 警告数量: {result['warning_count']}")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def validate_all_templates_in_directory(self, template_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        批量验证指定目录下的所有模板

        Args:
            template_dir: 模板目录路径

        Returns:
            Dict: 所有模板的验证结果
        """
        results = {}

        if not os.path.isdir(template_dir):
            print(f"❌ 目录不存在: {template_dir}")
            return results

        # 查找所有JSON文件
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, template_dir)
                    results[rel_path] = self.validate_template(file_path)

        return results

    def generate_batch_report(self, results: Dict[str, Dict[str, Any]]) -> str:
        """生成批量验证报告"""
        report_lines = []
        report_lines.append("\n" + "=" * 80)
        report_lines.append("批量模板验证报告")
        report_lines.append("=" * 80)

        valid_count = sum(1 for r in results.values() if r['is_valid'])
        invalid_count = len(results) - valid_count

        report_lines.append(f"\n📊 总体统计:")
        report_lines.append(f"  • 总模板数: {len(results)}")
        report_lines.append(f"  • 通过验证: {valid_count}")
        report_lines.append(f"  • 验证失败: {invalid_count}")

        # 按模板类型分组
        by_type = {}
        for file_path, result in results.items():
            template_type = result.get('template_type_name', '未识别')
            if template_type not in by_type:
                by_type[template_type] = []
            by_type[template_type].append((file_path, result))

        report_lines.append(f"\n📁 按模板类型分类:")
        for template_type, items in sorted(by_type.items()):
            valid = sum(1 for _, r in items if r['is_valid'])
            report_lines.append(f"  • {template_type}: {len(items)}个 (✅ {valid}个通过)")

            for file_path, result in items:
                status = "✅" if result['is_valid'] else "❌"
                report_lines.append(f"    {status} {file_path}")
                if result['errors']:
                    for error in result['errors'][:2]:  # 只显示前两个错误
                        report_lines.append(f"       • {error}")

        report_lines.append("\n" + "=" * 80)
        return "\n".join(report_lines)


def validate_template_file(file_path: str) -> str:
    """
    验证单个模板文件并返回格式化的报告

    Args:
        file_path: 模板文件路径

    Returns:
        str: 格式化的验证报告
    """
    validator = TemplateValidator()
    result = validator.validate_template(file_path)
    return validator.format_validation_report(result)


def validate_template_content(content: str, filename: str = "模板内容") -> str:
    """
    验证模板内容并返回格式化的报告

    Args:
        content: JSON内容字符串
        filename: 文件名（用于错误提示）

    Returns:
        str: 格式化的验证报告
    """
    validator = TemplateValidator()

    try:
        template_data = json.loads(content)
        # 自动检测模板类型
        validator.detected_template_type = validator.detect_template_type(template_data)
        # 执行验证
        validator._validate_basic_structure(template_data)
        validator._validate_required_fields(template_data)
        validator._validate_field_types(template_data)
        validator._validate_template_specific(template_data)

        if validator.detected_template_type:
            validator._validate_by_template_type(template_data)
    except json.JSONDecodeError as e:
        validator.errors.append(f"JSON格式错误: {str(e)}")
    except Exception as e:
        validator.errors.append(f"验证过程中发生未知错误: {str(e)}")

    result = validator._get_result()
    return validator.format_validation_report(result)


# 使用示例
if __name__ == "__main__":
    import sys
    import io

    # 修复编码问题
    if sys.platform == 'win32':
        import os
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # 重定向stdout为UTF-8
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("医疗器械模板识别验证工具")
    print("=" * 60)

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        # 如果是目录，批量验证
        if os.path.isdir(arg):
            print(f"\n开始批量验证目录: {arg}\n")
            validator = TemplateValidator()
            results = validator.validate_all_templates_in_directory(arg)
            report = validator.generate_batch_report(results)
            print(report)
        # 如果是文件，验证单个文件
        else:
            report = validate_template_file(arg)
            print(report)
    else:
        print("\n用法:")
        print("  单个验证: python template_validator.py <模板文件路径>")
        print("  批量验证: python template_validator.py <模板目录路径>")
        print("\n示例验证结果:\n")
        # 示例模板内容
        example_template = '''
{
    "name": "有源产品通用模板",
    "description": "适用于有源类产品",
    "version": "1.0.0",
    "created_date": "2025-09-26",
    "author": "医疗器械文件重命名工具",
    "rules": {
        "医疗器械注册申请表": {
            "keywords": ["医疗器械注册申请表", "注册申请表", "申请表"],
            "folders": ["1.监管信息-1.2申请表"],
            "tag": "#医疗器械注册申请表#"
        },
        "产品列表": {
            "keywords": ["产品列表"],
            "folders": ["1.监管信息-1.4产品列表"],
            "tag": "#产品列表#"
        }
    }
}
        '''
        report = validate_template_content(example_template, "示例模板")
        print(report)