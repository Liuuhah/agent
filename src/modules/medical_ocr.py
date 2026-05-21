"""
医疗病历 OCR 识别服务模块

职责：
- 接收图片路径，执行 OCR 识别
- 返回原始文本内容
- 处理基础的文件校验与异常
"""

import os
from pathlib import Path

# 尝试导入 PaddleOCR，如果未安装则提供 Mock 模式
try:
    from paddleocr import PaddleOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("[WARN] PaddleOCR not installed. Using Mock OCR mode for prototyping.")


class MedicalOCRService:
    """医疗病历 OCR 识别服务"""

    def __init__(self, use_angle_cls=True, lang="ch"):
        """初始化 OCR 引擎"""
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self.engine = None
        
        if OCR_AVAILABLE:
            # 初始化 PaddleOCR (首次运行会自动下载模型)
            self.engine = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang)

    def process_medical_image(self, image_path: str) -> str:
        """
        API-001: 处理病历图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: 识别出的原始文本
        """
        # 1. 校验文件是否存在
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # 2. 校验文件格式
        if path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
            raise ValueError(f"Unsupported image format: {path.suffix}. Please use .jpg or .png")

        # 3. 执行识别
        try:
            if self.engine:
                result = self.engine.ocr(str(path), cls=self.use_angle_cls)
                # PaddleOCR 返回的是嵌套列表，需要拼接文本
                raw_text = ""
                for line in result:
                    if line:
                        for word in line:
                            raw_text += word[1][0] + "\n"
                return self._clean_text(raw_text)
            else:
                return self._mock_ocr(image_path)
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")

    def _clean_text(self, text: str) -> str:
        """基础文本清洗"""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _mock_ocr(self, image_path: str) -> str:
        """Mock 识别结果（用于无 PaddleOCR 环境下的原型测试）
        
        模拟血常规化验单识别结果
        """
        return (
            "三分类血常规化验结果单\n"
            "单据编号：TEST20260513\n"
            "宠物名称：花宝\n"
            "宠物品种：猫/梨花猫\n"
            "宠物性别：雌绝\n"
            "体重(KG)：3.4\n"
            "客户姓名：李女士\n"
            "宠物年龄：2岁0个月\n"
            "\n"
            "化验名称           单位      下限    上限    结果    值标记\n"
            "白细胞数目(WBC)    X10^9/L   5.500   19.500  33.63   ↑\n"
            "Lymph#淋巴细胞数目 X10^9/L   0.800   7.000   9.6     ↑\n"
            "Mon#单核细胞数目   X10^9/L   0.010   1.900   0.68\n"
            "Gran中性粒细胞数目 X10^9/L   2.100   15.000  15.6    ↑\n"
            "Lymph%淋巴细胞百分%          12.000  45.000  65.3    ↑\n"
            "Mon%单核细胞百分比%          2.000   9.000   8.6\n"
            "RBC红细胞数目(猫)  X10^12/L  124.600 10.000  12.65\n"
            "血红蛋白(HGB)猫    g/L       80.000  150.00  145\n"
            "红细胞压积(HCT)%             26.000  47.000  36\n"
            "平均红细胞体积(MCV)fL        39.000  55.000  45.89\n"
            "平均红细胞血红蛋白pg         13.000  21.000  15.3\n"
            "平均红细胞血红蛋白浓度g/L    300.000 360.00  268     ↓\n"
            "血小板数目(PLT)    X10^9/L   100.000 518.00  360\n"
            "\n"
            "检验员：张医生\n"
            "检测日期：2026-05-13"
        )
