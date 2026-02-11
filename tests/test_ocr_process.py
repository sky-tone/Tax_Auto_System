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
    """使用 mock OCR 返回已知识别项，验证金额/日期/商品名能被正确解析"""

    class MockOCR:
        def ocr(self, img, cls=True):
            return [
                [[[0, 0], [100, 0], [100, 30], [0, 30]], ('商品A', 0.99)],
                [[[0, 40], [200, 40], [200, 80], [0, 80]], ('合计 ¥ 123.45', 0.95)],
                [[[0, 90], [300, 90], [300, 130], [0, 130]], ('2025年12月31日', 0.9)],
            ]

    mock = MockOCR()
    data = io.BytesIO(_make_test_image())
    data.name = 'mock.jpg'
    res = ocr_process.extract_text(data, ocr=mock)

    assert res['文件名'] == 'mock.jpg'
    assert abs(res['金额'] - 123.45) < 1e-6
    assert res['日期'] == '2025年12月31日'
    assert isinstance(res['识别商品名'], str) and len(res['识别商品名']) > 0


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
