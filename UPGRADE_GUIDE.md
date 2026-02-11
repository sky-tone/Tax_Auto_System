# 快速升级指南 - v2.0 发票字段提取与 PDF 支持

## 什么是新增功能？

智能税务记账系统升级到 v2.0，增加了以下功能：

### 1️⃣ 发票字段识别扩展
从 4 个字段扩展到 9 个，新增：
- ✅ 发票号（Invoice Number）
- ✅ 发票代码（Invoice Code）
- ✅ 开票机构（Seller/Issuer）
- ✅ 购方（Buyer）
- ✅ 税额（Tax Amount）

### 2️⃣ PDF 文件支持
现在可以直接上传 PDF 发票，系统会自动转换并识别。

### 3️⃣ 更智能的识别
使用正则表达式精准匹配发票特定字段。

---

## 升级步骤

### 步骤 1：更新依赖（可选但推荐）

```bash
# 安装 PDF 支持库
pip install pdf2image Pillow

# 或者如果你有 requirements-paddle.txt
pip install -r requirements-paddle.txt
```

### 步骤 2：运行测试验证升级

```bash
# 运行演示脚本
python test_invoice_extraction.py

# 运行单元测试
pytest tests/test_ocr_process.py -v
```

### 步骤 3：更新你的代码（如果有自定义代码）

#### 如果你直接调用 `extract_text()`：

**升级前：**
```python
result = ocr_process.extract_text(file)
print(result['文件名'])
print(result['金额'])
print(result['日期'])
```

**升级后（完全兼容）：**
```python
# 旧代码无需任何改动，完全兼容！
result = ocr_process.extract_text(file)
print(result['文件名'])      # 仍然有效
print(result['金额'])         # 仍然有效
print(result['日期'])         # 仍然有效

# 新增：可以使用新的字段
print(result['发票号'])       # NEW
print(result['开票机构'])     # NEW
print(result['税额'])         # NEW
```

#### 如果你在 Streamlit 中使用：

**升级前：**
```python
st.file_uploader("请上传图片/PDF", type=['png', 'jpg', 'jpeg'])
```

**升级后：**
```python
# app.py 已自动更新，您无需手动修改
# 但如果有自定义代码，更新为：
st.file_uploader("请上传图片或 PDF", type=['png', 'jpg', 'jpeg', 'pdf'])
```

---

## 重要：向后兼容性 ✅

**好消息：所有更改都是 100% 向后兼容的！**

- 🔄 旧的 4 个字段（文件名、商品名、金额、日期）仍然存在
- 🆕 新增的 5 个字段默认为 `None`（如果识别不到）
- ✅ 旧代码不需要任何修改就能继续工作

---

## 常见问题

### Q: 我需要升级吗？
**A:** 不是强制的，但强烈推荐，因为可以获得更多的发票信息。

### Q: 我的旧代码会破坏吗？
**A:** 不会。所有更改都是向后兼容的。旧代码可以直接运行。

### Q: PDF 不支持怎么办？
**A:** 如果 `pdf2image` 未安装，系统会返回友好的错误提示。按照提示安装即可。

### Q: 为什么有些字段识别不到？
**A:** 取决于：
1. 您的发票格式是否包含对应的关键词（如"发票号"、"开票机构"等）
2. OCR 的识别准确度

如果识别不到，可以手动调整 `utils/ocr_process.py` 中的正则表达式。

---

## 主要文件变更

| 文件 | 变更 | 影响范围 |
|------|------|--------|
| `utils/ocr_process.py` | 新增 5 个正则表达式 + 字段提取逻辑 | 核心功能 |
| `app.py` | 支持 PDF 上传 + 显示 9 个字段 | UI 展示 |
| `requirements-paddle.txt` | 新增 `pdf2image` | 依赖管理 |
| `tests/test_ocr_process.py` | 新增 3 个测试用例 | 测试覆盖 |

---

## 验证升级成功

运行以下命令验证升级是否成功：

```bash
# 1. 运行演示脚本
python test_invoice_extraction.py
# 应该看到：✓ 所有测试通过！

# 2. 运行单元测试
pytest tests/test_ocr_process.py -v
# 应该看到：6 passed

# 3. 启动 Streamlit（可选）
streamlit run app.py
```

---

## 下一步

现在您可以：

1. 📤 上传 PDF 发票（之前不支持）
2. 📋 获取更多发票信息（发票号、税额等）
3. 🔍 使用这些信息进行更精细的会计分类

---

## 需要帮助？

如有问题，请查看：
- [INVOICE_FIELDS_UPDATE.md](./INVOICE_FIELDS_UPDATE.md) - 详细文档
- [tests/test_ocr_process.py](./tests/test_ocr_process.py) - 使用示例
- [test_invoice_extraction.py](./test_invoice_extraction.py) - 功能演示

---

**祝升级愉快！🎉**
