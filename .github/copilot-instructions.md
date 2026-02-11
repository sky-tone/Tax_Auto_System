﻿# Copilot / AI Agent 使用说明（仓库特定）

目的：让 AI 代码代理快速上手本仓库的核心代码、约定与常用开发/调试命令。

概览
- UI: `app.py` (Streamlit) 负责文件上传与展示，调用 OCR + 规则映射生成会计科目。
- OCR: `utils/ocr_process.py` 负责 PaddleOCR 的懒加载、兼容性补丁、以及 `extract_text()` 的文本/金额/日期/商品名抽取逻辑。
- 规则: `utils/accounting_rules.py` 使用按序匹配的 `_RULES` 列表将商品名映射到 `会计科目`。
- 测试: `tests/test_ocr_process.py` 展示如何用 `ocr` 参数注入 Mock OCR 与 `monkeypatch` 保护环境。

重要约定（必须遵守）
- 懒加载：绝不要在模块导入时强制初始化 PaddleOCR。请使用 `get_ocr()` 或 `configure_ocr()` 进行显式/懒初始化以避免导入时阻塞或在无 Paddle 环境崩溃。
- PaddleOCR 与 Mock 区分：`get_ocr()` 在 PaddleOCR 未安装时返回 `None`（调用方可据此决定行为）。只有在初始化失败时才会创建 `MockOCR` 回退；不要假设 `get_ocr()` 总是返回一个 mock。
- 兼容性补丁：`utils/ocr_process.py` 包含对旧/新 paddle API 的补丁（例如为 `AnalysisConfig.set_optimization_level` 提供兼容实现）。在修改时保留这些补丁或等价保护以避免在不同 paddle 版本引入 AttributeError。
- 输入多态：`extract_text(image_file, ocr=None)` 必须继续支持三种输入：类文件对象（有 `.read()`，可带 `.name`）、`bytes`/`bytearray`，或文件路径字符串。
- 输出结构：保持向后兼容，返回字典需包含字段：`文件名`、`识别商品名`、`金额`、`日期`。当 OCR 不可用或发生异常时，返回中应包含 `错误` 或 `警告` 字段（测试和 `app.py` 依赖这些字段）。

解析策略（代码中的具体行为）
- 金额：优先匹配含关键词（金额/合计/总计/¥/￥）的文本；若无关键词，则选择识别出的最大数值候选。
- 日期：优先匹配 `YYYY年M月D日` 格式，其次匹配 `YYYY-M-D` 或 `YYYY/M/D`。
- 商品名：默认取最大字号（bbox 高度）文本；若存在金额，尝试选择距离金额最近且非数字的文本（长度 >=2）。

测试与本地开发提示
- 运行开发界面：在虚拟环境中运行 `streamlit run app.py`。
- 运行测试：`pytest tests/`。测试会在缺少 `cv2` 时跳过或可用 `monkeypatch` 注入 MockOCR（参见 `tests/test_ocr_process.py`）。
- 在 CI/开发机上避免安装 PaddleOCR：用 `ocr` 参数注入 Mock 对象或在测试中设置 `ocr_process.PaddleOCR = None` 并 `ocr_process._ocr = None` 来模拟未安装场景。

快速示例（测试中常用）
```python
# 注入 mock OCR（见 tests/test_ocr_process.py）
````instructions
﻿# Copilot / AI Agent 使用说明（仓库特定）

目的：让 AI 代码代理快速上手本仓库的核心代码、约定与常用开发/调试命令。

概览
- UI: `app.py` (Streamlit) 负责文件上传与展示，调用 OCR + 规则映射生成会计科目。
- OCR: `utils/ocr_process.py` 负责 PaddleOCR 的懒加载、兼容性补丁、以及 `extract_text()` 的文本/金额/日期/商品名抽取逻辑。
- 规则: `utils/accounting_rules.py` 使用按序匹配的 `_RULES` 列表将商品名映射到 `会计科目`。
- 测试: `tests/test_ocr_process.py` 展示如何用 `ocr` 参数注入 Mock OCR 与 `monkeypatch` 保护环境。

重要约定（必须遵守）
- 懒加载：绝不要在模块导入时强制初始化 PaddleOCR。请使用 `get_ocr()` 或 `configure_ocr()` 进行显式/懒初始化以避免导入时阻塞或在无 Paddle 环境崩溃。
- PaddleOCR 与 Mock 区分：`get_ocr()` 在 PaddleOCR 未安装时返回 `None`（调用方可据此决定行为）。只有在初始化失败时才会创建 `MockOCR` 回退；不要假设 `get_ocr()` 总是返回一个 mock。
- 兼容性补丁：`utils/ocr_process.py` 包含对旧/新 paddle API 的补丁（例如为 `AnalysisConfig.set_optimization_level` 提供兼容实现）。在修改时保留这些补丁或等价保护以避免在不同 paddle 版本引入 AttributeError。
- 输入多态：`extract_text(image_file, ocr=None)` 必须继续支持三种输入：类文件对象（有 `.read()`，可带 `.name`）、`bytes`/`bytearray`，或文件路径字符串。
- 输出结构：保持向后兼容，返回字典需包含字段：`文件名`、`识别商品名`、`金额`、`日期`。当 OCR 不可用或发生异常时，返回中应包含 `错误` 或 `警告` 字段（测试和 `app.py` 依赖这些字段）。

解析策略（代码中的具体行为）
- 金额：优先匹配含关键词（金额/合计/总计/¥/￥）的文本；若无关键词，则选择识别出的最大数值候选。
- 日期：优先匹配 `YYYY年M月D日` 格式，其次匹配 `YYYY-M-D` 或 `YYYY/M/D`。
- 商品名：默认取最大字号（bbox 高度）文本；若存在金额，尝试选择距离金额最近且非数字的文本（长度 >=2）。

测试与本地开发提示
- 运行开发界面：在虚拟环境中运行 `streamlit run app.py`。
- 运行测试：`pytest tests/`。测试会在缺少 `cv2` 时跳过或可用 `monkeypatch` 注入 MockOCR（参见 `tests/test_ocr_process.py`）。
- 在 CI/开发机上避免安装 PaddleOCR：用 `ocr` 参数注入 Mock 对象或在测试中设置 `ocr_process.PaddleOCR = None` 并 `ocr_process._ocr = None` 来模拟未安装场景。

快速示例（测试中常用）
```python
# 注入 mock OCR（见 tests/test_ocr_process.py）
mock = MyMockOCR()
res = ocr_process.extract_text(data, ocr=mock)
assert '金额' in res and '识别商品名' in res
```

关键文件速览
- 入口 UI: [app.py](app.py)
- OCR 实现: [utils/ocr_process.py](utils/ocr_process.py)
- 会计规则: [utils/accounting_rules.py](utils/accounting_rules.py)
- 测试示例: [tests/test_ocr_process.py](tests/test_ocr_process.py)
- Docker helper: [docker/Dockerfile](docker/Dockerfile) (镜像基于 `paddlepaddle/paddle:3.3.0`)

- Optional Paddle integration: see `requirements-paddle.txt` (root) and
	[.github/workflows/paddle-integration.yml](.github/workflows/paddle-integration.yml). The
	workflow provides a `workflow_dispatch` manual trigger that installs the optional
	Paddle/PaddleOCR dependencies and runs `verify_paddleocr.py` plus a light test.

如果需要，我可以进一步：
- 添加更多单元测试来覆盖兼容性补丁路径；
- 抽取并文档化 OCR 初始化策略；
- 或把规则映射（`_RULES`）迁移到可配置的 JSON/YAML 文件以便维护。

请审阅并告诉我是否需要补充具体示例或扩展测试场景。

````
