# Word转PDF功能 - 保留原文件设置说明

## 功能说明

Word转PDF转换功能支持设置是否保留原Word文件：

- **保留原文件 (keep_original_files: true)**：转换后保留原Word文件
- **删除原文件 (keep_original_files: false)**：转换后删除原Word文件，只保留PDF

## 当前设置

默认设置：**保留原文件** (`keep_original_files: true`)

## 如何修改设置

### 方法1：在规则管理中心修改（推荐）

1. 打开程序，点击 **"规则管理中心"** 按钮
2. 切换到 **"Word转PDF规则"** 标签页
3. 点击 **"编辑规则"** 按钮
4. 在左侧选择要编辑的模板（如"医疗器械文档转换1"）
5. 在右侧JSON编辑器中找到这一行：
   ```json
   "keep_original_files": true
   ```
6. 修改为：
   - `true` - 保留原文件
   - `false` - 删除原文件
7. 点击 **"保存"** 按钮
8. 选择该模板作为当前使用的Word转PDF规则

### 方法2：直接编辑模板文件

编辑模板文件（位于 `template/word_to_pdf_templates/` 目录）：

**医疗器械文档转换模板.json**:
```json
{
    "name": "医疗器械文档Word转PDF转换模板",
    "description": "适用于医疗器械文档的Word文件转PDF转换",
    "version": "1.0.0",
    "rules": {
        "医疗器械注册申请表": ["1.监管信息-1.2申请表"],
        ...
    },
    "keep_original_files": true  ← 修改这里
}
```

修改为：
- `"keep_original_files": true` - 保留原Word文件
- `"keep_original_files": false` - 转换后删除原Word文件

## 运行时确认

程序运行时会显示当前设置：

```
[START] 开始批量转换...
================================================================================
[CONFIG] 保留原文件设置: 是
================================================================================
```

或

```
[START] 开始批量转换...
================================================================================
[CONFIG] 保留原文件设置: 否（转换后将删除Word文件）
================================================================================
```

## 转换过程中的提示

### 如果设置为保留原文件 (true)

转换成功后会显示：
```
[OK] 转换成功! 文件大小: 123456 bytes
[SAVE] 保留原文件: 文档名称.docx
```

### 如果设置为删除原文件 (false)

转换成功后会显示：
```
[OK] 转换成功! 文件大小: 123456 bytes
[DELETE] 已删除原文件: 文档名称.docx
```

## 注意事项

### 1. 安全提示
- **删除原文件前请务必确认**：设置为 `false` 会永久删除Word文件
- **建议先备份**：首次使用删除功能前，建议备份原始文件
- **测试先行**：建议先用测试文件验证功能

### 2. 使用建议

**推荐保留原文件 (true) 的场景**：
- 首次转换，需要保留原始文档
- 可能需要再次编辑Word文件
- 文件作为备份存档

**可以删除原文件 (false) 的场景**：
- 确定只需要PDF格式
- 磁盘空间有限
- 已有备份的情况下

### 3. 特殊情况

- **PDF已存在**：如果目标位置已有同名PDF，会跳过该文件，不会删除Word文件
- **转换失败**：如果转换失败，不会删除Word文件
- **用户中断**：如果用户中断操作，不会删除已处理的Word文件

## 模板示例

### 保留原文件的模板
```json
{
    "name": "保留原文件模板",
    "description": "转换后保留Word文件",
    "version": "1.0.0",
    "created_date": "2025-10-15",
    "author": "用户",
    "rules": {
        "所有文档": [".*"]
    },
    "supported_formats": [".doc", ".docx"],
    "keep_original_files": true
}
```

### 删除原文件的模板
```json
{
    "name": "删除原文件模板",
    "description": "转换后删除Word文件，节省空间",
    "version": "1.0.0",
    "created_date": "2025-10-15",
    "author": "用户",
    "rules": {
        "所有文档": [".*"]
    },
    "supported_formats": [".doc", ".docx"],
    "keep_original_files": false
}
```

## 常见问题

### Q1: 我修改了设置但好像没生效？

**解决方法**：
1. 确认已保存模板文件
2. 在规则管理中心重新选择该模板
3. 关闭程序重新打开
4. 查看运行日志中的 `[CONFIG] 保留原文件设置` 信息

### Q2: 设置显示正确但行为不对？

**排查步骤**：
1. 查看日志中的 `[SAVE]` 或 `[DELETE]` 提示
2. 检查转换后文件夹中Word文件是否还在
3. 查看 `[INFO] 保留原文件设置` 日志

### Q3: 如何为不同类型文档设置不同的保留策略？

目前每个模板只有一个全局设置。如果需要不同策略：
1. 创建多个模板
2. 一个模板设置 `keep_original_files: true`
3. 另一个模板设置 `keep_original_files: false`
4. 根据需要切换使用不同的模板

## 技术细节

### 实现位置

**文件**: `final_word_to_pdf.py`

**关键代码**:
```python
# 第51行：默认设置
self.keep_original_files = True  # 默认保留原文件

# 第75-76行：从模板读取
self.keep_original_files = self.template_data.get('keep_original_files', True)
print(f"[INFO] 保留原文件设置: {'是' if self.keep_original_files else '否'}")

# 第251-259行：执行删除逻辑
if not self.keep_original_files:
    try:
        abs_word_path.unlink()
        print(f"[DELETE] 已删除原文件: {word_path.name}")
    except Exception as e:
        print(f"[WARNING] 删除原文件失败: {e}")
else:
    print(f"[SAVE] 保留原文件: {word_path.name}")
```

## 更新日志

**v1.0.1 (2025-10-15)**:
- ✅ 修复了重复代码导致的设置可能不生效的问题
- ✅ 添加了运行时配置显示
- ✅ 增强了日志输出
- ✅ 完善了文档说明

---

**最后更新**: 2025-10-15
**相关文件**: `final_word_to_pdf.py`, `template/word_to_pdf_templates/*.json`


