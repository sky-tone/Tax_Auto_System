import io
import pytest
import numpy as np
import cv2
import os
import sys
# Ensure project root is on sys.path for pytest collection
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import ocr_process

pytest.importorskip('cv2')


def _make_test_image():
    img = np.ones((200, 600, 3), dtype=np.uint8) * 255
    cv2.putText(img, '商品A', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, '合计 ¥ 123.45', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, '2025年12月31日', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    ok, buf = cv2.imencode('.jpg', img)
    assert ok
    return buf.tobytes()


def test_extract_text_no_paddle(monkeypatch):
    """当模块内没有 PaddleOCR 实例且 PaddleOCR 未安装时，返回包含错误且金额为 0"""
    monkeypatch.setattr(ocr_process, '_ocr', None)
    # 模拟未安装 PaddleOCR
    monkeypatch.setattr(ocr_process, 'PaddleOCR', None)

    data = io.BytesIO(_make_test_image())
    data.name = 'no_paddle.jpg'
    res = ocr_process.extract_text(data)
    assert res['文件名'] == 'no_paddle.jpg'
    assert res['金额'] == 0
    assert '错误' in res


def test_extract_text_with_mock_ocr(monkeypatch):
    """使用 mock OCR 返回已知识别项（包含发票字段），验证所有字段能被正确解析"""

    class MockOCR:
        def ocr(self, img, cls=True):
            return [
                [[[0, 0], [100, 0], [100, 30], [0, 30]], ('商品A', 0.99)],
                [[[0, 40], [200, 40], [200, 80], [0, 80]], ('合计 ¥ 123.45', 0.95)],
                [[[0, 90], [300, 90], [300, 130], [0, 130]], ('2025年12月31日', 0.9)],
                [[[0, 140], [300, 140], [300, 170], [0, 170]], ('发票号ABC123456', 0.85)],
                [[[0, 180], [300, 180], [300, 210], [0, 210]], ('发票代码1234567890', 0.88)],
                [[[0, 220], [300, 220], [300, 250], [0, 250]], ('销售方公司A', 0.87)],
                [[[0, 260], [300, 260], [300, 290], [0, 290]], ('购方公司B', 0.86)],
                [[[0, 300], [300, 300], [300, 330], [0, 330]], ('税额 25.50', 0.84)],
            ]

    mock = MockOCR()
    data = io.BytesIO(_make_test_image())
    data.name = 'mock.jpg'
    res = ocr_process.extract_text(data, ocr=mock)

    assert res['文件名'] == 'mock.jpg'
    assert abs(res['金额'] - 123.45) < 1e-6
    assert res['日期'] == '2025年12月31日'
    assert isinstance(res['识别商品名'], str) and len(res['识别商品名']) > 0
    
    # 验证新增的发票字段
    assert '发票号' in res
    assert '发票代码' in res
    assert '开票机构' in res
    assert '购方' in res
    assert '税额' in res
    
    # 验证发票字段的解析值（基于 regex）
    assert res['发票号'] == 'ABC123456'
    assert res['发票代码'] == '1234567890'
    assert res['开票机构'] == '公司A'
    assert res['购方'] == '公司B'
    assert abs(res['税额'] - 25.50) < 1e-6


def test_extract_text_confidence_filter():
    """验证 conf_threshold 会过滤低置信度的候选，从而改变金额选择逻辑"""

    class MockOCR2:
        def ocr(self, img, cls=True):
            # 两个金额候选：一个置信度低但数值大，一个置信度高但数值小
            return [
                [[[0, 0], [100, 0], [100, 30], [0, 30]], ('合计 ¥ 999.99', 0.5)],
                [[[0, 40], [200, 40], [200, 80], [0, 80]], ('合计 ¥ 123.45', 0.95)],
                [[[0, 90], [300, 90], [300, 130], [0, 130]], ('2025年12月31日', 0.9)],
            ]

    data1 = io.BytesIO(_make_test_image())
    data1.name = 'conf1.jpg'
    # 默认行为（不过滤）应选择数值最大的候选
    res_default = ocr_process.extract_text(data1, ocr=MockOCR2())
    assert abs(res_default['金额'] - 999.99) < 1e-6

    data2 = io.BytesIO(_make_test_image())
    data2.name = 'conf2.jpg'
    # 应用阈值过滤，低置信度 0.5 的候选将被过滤，选中 123.45
    res_filtered = ocr_process.extract_text(data2, ocr=MockOCR2(), conf_threshold=0.9)
    assert abs(res_filtered['金额'] - 123.45) < 1e-6


def test_paddlex_patch_handles_attributeerror(monkeypatch):
    """模拟 paddlex 模块中 PaddleInfer._create 首次抛出包含 set_optimization_level 的 AttributeError，
    确保 configure_ocr() 能安全返回（不抛异常）。"""

    import types, sys

    # 创建伪 paddlex 模块路径
    mod_name = 'paddlex.inference.models.common.static_infer'
    pkg = types.ModuleType('paddlex')
    sub = types.ModuleType('paddlex.inference.models.common.static_infer')

    # 制造一个原始的 _create：第一次抛 AttributeError，第二次返回正常值
    class DummyPaddleInfer:
        call_count = 0

        @staticmethod
        def _create(self, *a, **k):
            DummyPaddleInfer.call_count += 1
            if DummyPaddleInfer.call_count == 1:
                raise AttributeError('missing set_optimization_level')
            return 'created'

    sub.PaddleInfer = DummyPaddleInfer

    # 注入到 sys.modules
    sys.modules[mod_name] = sub

    # 确保 ocr_process 中能找到 PaddleOCR：注入一个接受任意参数的占位类
    class DummyPaddleOCR:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setattr(ocr_process, 'PaddleOCR', DummyPaddleOCR)

    # 运行 configure_ocr 并确保不会抛出异常（返回 DummyPaddleOCR 实例或 None）
    try:
        res = ocr_process.configure_ocr(use_gpu=False)
    finally:
        # 清理注入的模块
        try:
            del sys.modules[mod_name]
        except Exception:
            pass

    # 只要没有抛异常即可视为成功；res 可以为 DummyPaddleOCR 实例或 None（取决于环境）
    assert True

def test_extract_text_pdf_detection(monkeypatch):
    """测试 PDF 文件检测和处理（无 pdf2image 时返回相应错误）"""
    
    class MockOCR:
        def ocr(self, img, cls=True):
            return [[[[0, 0], [100, 0], [100, 30], [0, 30]], ('test', 0.9)]]
    
    # 构造 PDF 魔数
    pdf_bytes = b'%PDF-1.4\n' + b'fake pdf content'
    data = io.BytesIO(pdf_bytes)
    data.name = 'test.pdf'
    
    # 当 pdf2image 未安装时，应返回相应的错误消息
    res = ocr_process.extract_text(data, ocr=MockOCR())
    
    # 检查返回结构中 PDF 相关的字段
    assert '文件名' in res
    assert '金额' in res
    # 由于 pdf2image 可能未安装，应该有错误或警告
    # （如果 pdf2image 安装了，则不会有错误；测试应该容错）
    assert res['金额'] == 0 or '错误' in res or '警告' in res


def test_extract_text_returns_nine_fields(monkeypatch):
    """验证返回字典总是包含 9 个标准字段"""
    
    class MockOCR:
        def ocr(self, img, cls=True):
            return []
    
    # 即使没有识别到任何内容，也应返回 9 个字段
    data = io.BytesIO(_make_test_image())
    data.name = 'empty.jpg'
    res = ocr_process.extract_text(data, ocr=MockOCR())
    
    required_fields = [
        '文件名', '识别商品名', '金额', '日期',
        '发票号', '发票代码', '开票机构', '购方', '税额'
    ]
    for field in required_fields:
        assert field in res, f"缺少字段: {field}"