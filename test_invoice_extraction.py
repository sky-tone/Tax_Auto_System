#!/usr/bin/env python3
"""
演示脚本：展示新增的发票字段提取功能
"""

import io
import numpy as np
import cv2
from utils import ocr_process


def create_test_invoice_image():
    """创建一个模拟发票图片用于测试"""
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # 绘制模拟发票内容
    texts = [
        ('发票号：AB2025123456', (50, 100)),
        ('发票代码：1234567890', (50, 150)),
        ('开票机构：北京某税务所', (50, 200)),
        ('购方：南京公司B', (50, 250)),
        ('金额：¥ 2500.50', (50, 300)),
        ('税额：250.05', (50, 350)),
        ('日期：2025年1月15日', (50, 400)),
        ('商品：办公用品', (50, 450)),
    ]
    
    for text, pos in texts:
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    ok, buf = cv2.imencode('.jpg', img)
    assert ok, "图片编码失败"
    return buf.tobytes()


def test_with_mock_ocr():
    """使用 Mock OCR 演示发票字段提取"""
    
    class DemoOCR:
        """模拟 OCR 返回发票相关的识别结果"""
        def ocr(self, img, cls=True):
            return [
                [[[50, 90], [350, 90], [350, 120], [50, 120]], ('发票号：AB2025123456', 0.95)],
                [[[50, 140], [350, 140], [350, 170], [50, 170]], ('发票代码：1234567890', 0.94)],
                [[[50, 190], [350, 190], [350, 220], [50, 220]], ('开票机构：北京某税务所', 0.92)],
                [[[50, 240], [350, 240], [350, 270], [50, 270]], ('购方：南京公司B', 0.91)],
                [[[50, 290], [350, 290], [350, 320], [50, 320]], ('金额：¥ 2500.50', 0.96)],
                [[[50, 340], [350, 340], [350, 370], [50, 370]], ('税额：250.05', 0.90)],
                [[[50, 390], [350, 390], [350, 420], [50, 420]], ('日期：2025年1月15日', 0.93)],
                [[[50, 440], [350, 440], [350, 470], [50, 470]], ('办公用品', 0.89)],
            ]
    
    # 创建图片数据
    image_bytes = create_test_invoice_image()
    data = io.BytesIO(image_bytes)
    data.name = 'test_invoice.jpg'
    
    # 使用 Mock OCR 进行提取
    print("=" * 60)
    print("发票字段提取演示")
    print("=" * 60)
    
    result = ocr_process.extract_text(data, ocr=DemoOCR())
    
    # 展示所有提取的字段
    print("\n提取结果：")
    print("-" * 60)
    for key, value in result.items():
        if value is not None:
            print(f"  {key:12}: {value}")
    
    print("\n" + "=" * 60)
    print("验证结果：")
    print("-" * 60)
    
    # 检查关键字段
    checks = [
        ('文件名', result.get('文件名') == 'test_invoice.jpg', '文件名正确'),
        ('金额', abs(result.get('金额', 0) - 2500.50) < 0.01, '金额正确'),
        ('发票号', result.get('发票号') == 'AB2025123456', '发票号正确'),
        ('发票代码', result.get('发票代码') == '1234567890', '发票代码正确'),
        ('开票机构', result.get('开票机构') == '北京某税务所', '开票机构正确'),
        ('购方', result.get('购方') == '南京公司B', '购方正确'),
        ('税额', abs(result.get('税额', 0) - 250.05) < 0.01, '税额正确'),
    ]
    
    for name, passed, desc in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}")
    
    all_passed = all(check[1] for check in checks)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)


if __name__ == '__main__':
    test_with_mock_ocr()
