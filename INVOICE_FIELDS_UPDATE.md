# 发票字段提取与 PDF 支持 - 功能更新文档

## 概述

本更新增强了智能税务记账系统的发票识别能力，包括：

1. **扩展字段提取**：从原来的 4 个字段（文件名、商品名、金额、日期）扩展到 9 个字段，新增发票号、发票代码、开票机构、购方、税额
2. **PDF 支持**：系统现在支持 PDF 发票文件的处理（通过 pdf2image 库将 PDF 页面转换为图像）
3. **智能识别**：使用正则表达式模式对发票特定字段进行智能识别和解析

---

## 功能详情

### 1. 扩展的返回字段结构

`extract_text()` 函数现在返回 9 个字段的字典：

| 字段 | 类型 | 说明 |
|------|------|------|
| `文件名` | str | 上传文件的原始名称 |
| `识别商品名` | str | OCR 识别出的最大字号文本或距离金额最近的文本 |
| `金额` | float | 提取的金额（优先取含"金额/合计/总计"关键词的值） |
| `日期` | str | 识别的日期（支持 YYYY年M月D日、YYYY-M-D、YYYY/M/D 格式） |
| `发票号` | str | 发票号码（通过正则匹配 "发票号/号码/No." 等关键词） |
| `发票代码` | str | 发票代码（通过正则匹配"发票代码"关键词） |
| `开票机构` | str | 销售方/开票机构名称 |
| `购方` | str | 购买方/购方名称 |
| `税额` | float | 税费金额 |

### 2. PDF 支持

系统现在支持处理 PDF 发票文件：

- **检测方式**：通过文件扩展名（`.pdf`）或 PDF 魔数（`%PDF`）检测
- **处理方式**：使用 `pdf2image` 库将 PDF 的第一页转换为 OpenCV 兼容的图像格式
- **错误处理**：
  - 如果 `pdf2image` 未安装，返回友好的错误提示，建议用户运行 `pip install pdf2image`
  - 如果 PDF 转换失败，返回包含错误信息的结果字典

### 3. 发票字段识别模式

系统使用以下正则表达式识别发票字段：

```python
# 发票号：匹配 "发票号/号码/No." 等后跟的字母数字组合
INVOICE_NUMBER_RE = re.compile(r"(?:发票号|发票代码|号码|No\.?)[\s：:]*([A-Z0-9\-]{6,30})")

# 发票代码：匹配 "发票代码" 后跟的 10-15 位数字
INVOICE_CODE_RE = re.compile(r"(?:发票代码)[\s：:]*([0-9]{10,15})")

# 销售方/开票机构
SELLER_RE = re.compile(r"(?:销售方|卖方|开票人|开票机构)[\s：:]*(.{2,20})")

# 购买方
BUYER_RE = re.compile(r"(?:购买方|买方|购方)[\s：:]*(.{2,20})")

# 税额
TAX_RE = re.compile(r"(?:税额|税|税率)[\s：:]*([0-9]+(?:\.[0-9]+)?)")
```

---

## 使用示例

### 处理图片文件

```python
from utils import ocr_process

# 上传图片文件
with open('invoice.jpg', 'rb') as f:
    result = ocr_process.extract_text(f)

# 结果包含所有 9 个字段
print(result['发票号'])      # 'AB2025123456'
print(result['开票机构'])     # '北京某税务所'
print(result['金额'])        # 2500.50
```

### 处理 PDF 文件

```python
# 上传 PDF 文件
with open('invoice.pdf', 'rb') as f:
    result = ocr_process.extract_text(f)

# 系统会自动转换 PDF 第一页为图像并进行识别
print(result['发票号'])
```

### 在 Streamlit 应用中使用

`app.py` 已更新以支持 PDF 上传和显示所有 9 个字段：

```python
# 侧边栏支持 PDF 上传
uploaded_files = st.file_uploader(
    "请上传图片或 PDF",
    accept_multiple_files=True,
    type=['png', 'jpg', 'jpeg', 'pdf']
)

# 结果表格自动显示所有字段
display_cols = [
    '文件名', '识别商品名', '金额', '日期',
    '发票号', '发票代码', '开票机构', '购方', '税额',
    '会计科目'
]
display_df = df[[col for col in display_cols if col in df.columns]]
st.dataframe(display_df, use_container_width=True)
```

---

## 依赖安装

### 基础依赖（已有）

```bash
pip install -r requirements.txt
```

### PDF 支持（新增）

如果需要处理 PDF 文件，请安装 PDF 相关库：

```bash
pip install pdf2image Pillow

# 在 Linux 上可能还需要安装系统依赖：
# sudo apt-get install poppler-utils (Debian/Ubuntu)
# brew install poppler (macOS)
```

或使用更新的 `requirements-paddle.txt`：

```bash
pip install -r requirements-paddle.txt
```

---

## 测试

### 运行单元测试

```bash
# 运行所有测试
pytest tests/test_ocr_process.py -v

# 运行特定测试
pytest tests/test_ocr_process.py::test_extract_text_with_mock_ocr -v
```

### 运行演示脚本

```bash
python test_invoice_extraction.py
```

该脚本演示了新增发票字段的提取功能，输出如下：

```
============================================================
发票字段提取演示
============================================================

提取结果：
------------------------------------------------------------
  文件名         : test_invoice.jpg
  识别商品名       : 办公用品
  金额          : 2500.5
  发票号         : AB2025123456
  发票代码        : 1234567890
  开票机构        : 北京某税务所
  购方          : 南京公司B
  税额          : 250.05

============================================================
验证结果：
------------------------------------------------------------
  ✓ 文件名正确
  ✓ 金额正确
  ✓ 发票号正确
  ✓ 发票代码正确
  ✓ 开票机构正确
  ✓ 购方正确
  ✓ 税额正确

============================================================
✓ 所有测试通过！
============================================================
```

---

## 后向兼容性

所有修改都保持了向后兼容性：

1. **函数签名**：`extract_text()` 的参数和调用方式未变
2. **返回结构**：新字段都有默认值（`None`），不会破坏现有代码
3. **旧版本支持**：即使旧版本的代码只读取 4 个原始字段，也能继续正常工作

---

## 常见问题

### Q: 如何处理 PDF2Image 不支持的系统？

A: 如果 `pdf2image` 无法安装（例如缺少 `poppler-utils`），系统会返回友好的错误提示。建议按照错误消息的指引安装相应的系统依赖。

### Q: 发票字段识别失败怎么办？

A: 识别结果取决于：
1. OCR 的识别准确度（由 PaddleOCR 决定）
2. 正则表达式是否匹配实际的发票格式

如果识别失败，可以：
- 检查 OCR 的原始识别结果（通过打印 `raw` 变量）
- 根据实际发票格式调整正则表达式
- 确保发票中包含识别关键词（如"发票号"、"发票代码"等）

### Q: 一张 PDF 有多个页面怎么处理？

A: 目前系统只处理 PDF 的第一页。如需处理多页，可以在 `extract_text()` 中扩展以下代码：

```python
# 现在：仅第一页
pages = convert_from_bytes(image_bytes, first_page=1, last_page=1)

# 扩展为多页（需要返回多个结果）
pages = convert_from_bytes(image_bytes)
for page in pages:
    # 处理每一页
```

---

## 相关文件

- [utils/ocr_process.py](../utils/ocr_process.py) - 核心 OCR 和字段提取逻辑
- [app.py](../app.py) - Streamlit UI（已更新以支持 PDF 和新字段）
- [tests/test_ocr_process.py](../tests/test_ocr_process.py) - 单元测试（包含新字段测试）
- [requirements-paddle.txt](../requirements-paddle.txt) - 完整依赖列表（包含 PDF 支持）
- [test_invoice_extraction.py](../test_invoice_extraction.py) - 功能演示脚本

---

## 后续改进方向

1. **多页 PDF 支持**：扩展以处理 PDF 的多个页面
2. **字段验证**：添加发票字段的有效性检查（如发票代码格式）
3. **规则配置化**：将硬编码的正则表达式迁移到 YAML/JSON 配置文件
4. **性能优化**：缓存 OCR 结果或使用异步处理
5. **UI 增强**：在 Streamlit 界面中显示 OCR 置信度和字段匹配结果

---

## 版本信息

- **更新日期**：2025 年
- **涉及版本**：v2.0+
- **PaddleOCR 版本**：3.3.0+
- **Python 版本**：3.8+
