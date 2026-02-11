"""utils.ocr_process
基于 PaddleOCR 的 OCR 工具封装（保留懒加载、兼容性与 Mock 回退）。

功能要点：
- 懒加载 PaddleOCR（通过 `get_ocr()` / `configure_ocr()`），默认中文模式 `lang='ch'`。
- `extract_text(image_file, ocr=None)` 支持文件对象 / bytes / 路径字符串输入，返回字典：
  `{'文件名', '识别商品名', '金额', '日期'}`，在错误场景下包含 `错误` 或 `警告` 字段。
"""

import io
import logging
import re
from typing import Optional, Dict, Any

import cv2
import numpy as np
import threading

try:
    from paddleocr import PaddleOCR
except Exception as e:
    PaddleOCR = None
    logging.getLogger(__name__).warning("无法导入 PaddleOCR：%s", e)

# 模块级 OCR 实例与状态
_ocr: Optional[object] = None
_ocr_is_mock: bool = False
_ocr_lock = threading.Lock()


class MockOCR:
    """轻量 Mock，用于测试或初始化失败时的回退（接口兼容 PaddleOCR）。"""

    is_mock = True

    def __init__(self, note: str = None):
        self._note = note

    def ocr(self, img, cls=True):
        logging.getLogger(__name__).warning("使用 MockOCR 回退：%s", self._note or "无详细信息")
        return []


def configure_ocr(use_gpu: bool = False, lang: str = 'ch', use_angle_cls: bool = True, **kwargs):
    """初始化或重配置模块级 PaddleOCR。

    返回已初始化的 PaddleOCR 实例，若 PaddleOCR 未安装返回 None。
    若初始化失败（参数不兼容等），返回 None（调用方可决定是否回退到 Mock）。
    """
    global _ocr, _ocr_is_mock
    _ocr_is_mock = False
    if PaddleOCR is None:
        logging.getLogger(__name__).warning("PaddleOCR 未安装，跳过初始化")
        _ocr = None
        return None

    # 兼容性补丁：尝试为不同 paddle 版本补充缺失的方法以降低初始化错误
    try:
        import paddle
        import paddle.base.libpaddle as _libpaddle
        ac = getattr(_libpaddle, 'AnalysisConfig', None)
        if ac is not None and not hasattr(ac, 'set_optimization_level'):
            if hasattr(ac, 'set_tensorrt_optimization_level'):
                def _set_opt(self, level):
                    try:
                        self.set_tensorrt_optimization_level(level)
                    except Exception:
                        pass
            else:
                def _set_opt(self, level):
                    pass
            try:
                setattr(ac, 'set_optimization_level', _set_opt)
                logging.getLogger(__name__).info("为 paddle.AnalysisConfig 添加兼容方法 set_optimization_level")
            except Exception:
                pass
    except Exception:
        # 忽略兼容补丁失败
        pass

    # 进一步兼容：如果存在 paddlex 的 PaddleInfer._create，包装以在遇到
    # set_optimization_level 的 AttributeError 时尝试补丁并重试（降级处理）
    try:
        import importlib
        px = importlib.import_module('paddlex.inference.models.common.static_infer')
        if hasattr(px, 'PaddleInfer') and getattr(px.PaddleInfer, '_create', None) is not None:
            orig = px.PaddleInfer._create

            def _patched_create(self, *a, **k):
                try:
                    return orig(self, *a, **k)
                except AttributeError as e:
                    if 'set_optimization_level' in str(e):
                        try:
                            import paddle.base.libpaddle as lib2
                            ac2 = getattr(lib2, 'AnalysisConfig', None)
                            if ac2 is not None and not hasattr(ac2, 'set_optimization_level'):
                                def _set_opt2(self, level):
                                    try:
                                        self.set_tensorrt_optimization_level(level)
                                    except Exception:
                                        pass
                                try:
                                    setattr(ac2, 'set_optimization_level', _set_opt2)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        # retry once
                        return orig(self, *a, **k)
                    raise

            try:
                px.PaddleInfer._create = _patched_create
            except Exception:
                pass
    except Exception:
        # 如果没有 paddlex 或补丁失败，不抛出错误
        pass

    # 构建 candidate 参数并只传给目标构造器支持的参数
    candidate = {'use_gpu': use_gpu, 'lang': lang, 'use_angle_cls': use_angle_cls}
    candidate.update(kwargs)

    # 兼容不同版本的 PaddleOCR 构造签名
    try:
        import inspect
        sig = inspect.signature(PaddleOCR.__init__)
        supported = {n for n in sig.parameters.keys() if n not in ('self', 'args', 'kwargs')}
        init_kwargs = {k: v for k, v in candidate.items() if k in supported}
    except Exception:
        init_kwargs = candidate

    # 使用锁保护初始化，避免并发环境重复初始化的竞态
    with _ocr_lock:
        try:
            # 记录环境版本便于诊断
            try:
                import paddle
                logging.getLogger(__name__).info("初始化 PaddleOCR：paddle=%s numpy=%s", getattr(paddle, '__version__', None), np.__version__)
            except Exception:
                logging.getLogger(__name__).info("初始化 PaddleOCR：numpy=%s", np.__version__)

            _ocr = PaddleOCR(**init_kwargs)
            _ocr_is_mock = getattr(_ocr, 'is_mock', False)
            return _ocr
        except TypeError:
            # 若某些参数不被支持，尝试剔除常见参数重试
            for key in ('use_gpu', 'use_angle_cls'):
                init_kwargs.pop(key, None)
            try:
                _ocr = PaddleOCR(**init_kwargs)
                _ocr_is_mock = getattr(_ocr, 'is_mock', False)
                return _ocr
            except Exception as e:
                logging.getLogger(__name__).warning("初始化 PaddleOCR 失败：%s", e)
                _ocr = None
                return None
        except Exception as e:
            logging.getLogger(__name__).warning("初始化 PaddleOCR 失败：%s", e)
            _ocr = None
            return None


def get_ocr(try_init: bool = True, **init_kwargs) -> Optional[object]:
    """返回模块级 OCR 实例（若未初始化且 try_init=True 尝试懒初始化）。

    注意：若 PaddleOCR 未安装，返回 None（允许调用方区分未安装与初始化失败）。
    """
    global _ocr, _ocr_is_mock
    if _ocr is not None:
        return _ocr
    if not try_init:
        return None
    if PaddleOCR is None:
        return None
    o = configure_ocr(**init_kwargs)
    if o is None:
        # 不强制创建 MockOCR，这里保留调用方区分未安装/初始化失败的权利
        logging.getLogger(__name__).warning("PaddleOCR 初始化失败或不兼容，返回 None（可由调用方回退为 MockOCR）")
        return None
    return o


AMOUNT_RE = re.compile(r"(?:金额|合计|总计|小计|¥|￥)?\s*([0-9]+(?:[\,\d]*\d)?(?:\.\d+)?)")
DATE_RE = re.compile(r"(\d{4}年\d{1,2}月\d{1,2}日)")
ALT_DATE_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
NUM_RE = re.compile(r"(\d+[\d,]*\.?\d*)")


def _bbox_center(bbox):
    xs = [p[0] for p in bbox]
    ys = [p[1] for p in bbox]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _bbox_height(bbox):
    ys = [p[1] for p in bbox]
    return max(ys) - min(ys)


def _parse_amount_from_text(text: str) -> Optional[float]:
    if not text:
        return None
    m = AMOUNT_RE.search(text)
    if m:
        num = m.group(1)
    else:
        m2 = NUM_RE.search(text)
        if m2:
            num = m2.group(1)
        else:
            return None
    try:
        return float(num.replace(',', ''))
    except Exception:
        return None


def extract_text(image_file, ocr=None, conf_threshold: float = 0.0) -> Dict[str, Any]:
    """读取图片并使用 PaddleOCR（或传入的 ocr 实例）识别，返回解析结果字典。

    支持三种输入：类文件对象（带 .read()，可含 .name）、bytes/bytearray、或文件路径字符串。
    若未传入 `ocr`，函数会尝试通过 `get_ocr()` 懒加载 PaddleOCR；若 PaddleOCR 未安装，返回包含 `错误` 的结果。
    """
    filename = getattr(image_file, 'name', 'uploaded_image')

    # 选择 OCR 实例：优先使用传入的 ocr（用于测试），否则尝试懒初始化
    local_ocr = ocr or get_ocr()
    is_mock = getattr(local_ocr, 'is_mock', False) if local_ocr is not None else False

    if local_ocr is None:
        return {"文件名": filename, "识别商品名": None, "金额": 0, "日期": None, "错误": "PaddleOCR 未安装或未初始化"}

    try:
        # 读取 bytes
        if hasattr(image_file, 'read'):
            image_bytes = image_file.read()
        elif isinstance(image_file, (bytes, bytearray)):
            image_bytes = bytes(image_file)
        else:
            with open(image_file, 'rb') as f:
                image_bytes = f.read()

        if not image_bytes:
            raise ValueError('空的图片数据')

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            if is_mock:
                return {"文件名": filename, "识别商品名": None, "金额": 0, "日期": None, "警告": "使用 MockOCR；图片解码失败"}
            raise ValueError('无法解码图片')

        raw = local_ocr.ocr(img, cls=True)

        entries = []
        for line in raw:
            if not line:
                continue
            bbox = line[0]
            text, conf = line[1]
            try:
                conf_val = float(conf)
            except Exception:
                conf_val = 0.0
            # 根据 conf_threshold 过滤低置信度识别结果
            if conf_val < (conf_threshold or 0.0):
                continue
            entries.append({
                'text': str(text).strip(),
                'conf': conf_val,
                'bbox': bbox,
                'center': _bbox_center(bbox),
                'height': _bbox_height(bbox),
            })

        # 解析金额
        found_amount = None
        amount_center = None
        candidates = []
        for e in entries:
            amt = _parse_amount_from_text(e['text'])
            if amt is not None:
                candidates.append((e, amt))
                if re.search(r'金额|合计|总计|小计|¥|￥', e['text']):
                    found_amount = amt
                    amount_center = e['center']
                    break
        if found_amount is None and candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            found_amount = candidates[0][1]
            amount_center = candidates[0][0]['center']

        # 解析日期
        found_date = None
        for e in entries:
            m = DATE_RE.search(e['text'])
            if m:
                found_date = m.group(1)
                break
        if found_date is None:
            for e in entries:
                m = ALT_DATE_RE.search(e['text'])
                if m:
                    found_date = m.group(1)
                    break

        # 识别商品名：首选最大字号；若存在金额，选最近的非数字文本
        product_name = None
        if entries:
            entries_sorted = sorted(entries, key=lambda x: x['height'], reverse=True)
            product_name = entries_sorted[0]['text'] if entries_sorted else None
            if amount_center is not None:
                def dist(a, b):
                    return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

                non_num = [e for e in entries if _parse_amount_from_text(e['text']) is None and e['text']]
                if non_num:
                    nearest = min(non_num, key=lambda e: dist(e['center'], amount_center))
                    if len(nearest['text']) >= 2:
                        product_name = nearest['text']

        if found_amount is None:
            found_amount = 0

        out = {'文件名': filename, '识别商品名': product_name, '金额': found_amount, '日期': found_date}
        if is_mock:
            out['警告'] = 'OCR 使用 Mock 回退；结果仅供调试'
        return out

    except Exception as e:
        logging.getLogger(__name__).exception('OCR 识别失败：%s', e)
        return {"文件名": filename, "识别商品名": None, "金额": 0, "日期": None, "错误": str(e)}
