# 医疗器械文档处理工具

一款专为医疗器械注册申报人员设计的文档批量处理工具，提供 ZIP 解压、文件夹清理、Word 转 PDF、文件重命名、PDF 合并等功能。

## ✨ 功能特性

- **ZIP 批量解压** - 自动解压并修复中文文件名乱码问题
- **文件夹清理** - 根据规则清理文件夹，只保留材料包
- **文件夹提取** - 按模板提取指定文件夹到 output 目录
- **Word 转 PDF** - 批量转换 .doc/.docx 文件为 PDF 格式
- **文件重命名** - 根据模板为文件添加标识标签
- **PDF 合并** - 选择文件、设置顺序进行合并
- **自动化流程** - 支持完整流程一键执行或自定义流程组合

## 📋 系统要求

- Windows 7/8/10/11
- Python 3.7+（开发环境）
- Microsoft Word（Word 转 PDF 功能需要）
- 内存 ≥ 2GB
- 磁盘空间 ≥ 100MB

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python run_gui.py
```

### 打包为 EXE

```bash
python build_exe_optimized.py
```

## 📁 项目结构

```
├── main_gui.py              # 主程序 GUI 界面
├── run_gui.py               # 启动脚本
├── analyze_zip_encoding.py  # ZIP 解压模块
├── clean_folder.py          # 文件夹清理模块
├── extract_folders.py       # 文件夹提取模块
├── final_word_to_pdf.py     # Word 转 PDF 模块
├── universal_rename.py      # 文件重命名模块
├── pdf_merger.py            # PDF 合并模块
├── template/                # 规则模板目录
│   ├── clean_templates/     # 清理规则模板
│   ├── rename_templates/    # 重命名规则模板
│   ├── folder_templates/    # 文件夹提取模板
│   └── word_to_pdf_templates/  # Word 转 PDF 模板
├── data/                    # 待处理文件目录
└── requirements.txt         # 依赖包列表
```

## 📖 使用说明

1. 将待处理的材料包放入 `data/` 文件夹
2. 运行程序，选择需要的功能
3. 可使用「完整自动化流程」一键处理，或选择单独功能执行
4. 在「规则管理」中可配置各功能的处理规则

## 🔧 模板配置

各功能支持 JSON 模板配置，模板文件位于 `template/` 目录下。可根据实际需求修改模板规则。

## 📄 License

MIT License

## 👤 作者

Lxx
