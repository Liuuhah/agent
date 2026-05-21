"""
主类：PetHealthAdvisor

职责：
- 组合所有 Mixin
- 初始化 ChatCompressClient
- 提供公共 API
"""

import sys
import logging
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 添加当前目录以支持直接运行
current_dir = Path(__file__).parent
if str(current_dir.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent))

from ai_assistant.chat_compress_client import ChatCompressClient

# 配置日志
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'pet_health_advisor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PetHealthAdvisor')


# 支持直接运行和包导入两种方式
try:
    from ._prompt_engine import PromptEngineMixin
    from ._business_logic import BusinessLogicMixin
    from ._consultation import ConsultationMixin
    from ._extraction import ExtractionMixin
    from ._fallback import FallbackMixin
    from ._utils import UtilsMixin
except ImportError:
    # 直接运行时使用绝对导入
    from pet_health_advisor._prompt_engine import PromptEngineMixin
    from pet_health_advisor._business_logic import BusinessLogicMixin
    from pet_health_advisor._consultation import ConsultationMixin
    from pet_health_advisor._extraction import ExtractionMixin
    from pet_health_advisor._fallback import FallbackMixin
    from pet_health_advisor._utils import UtilsMixin


class PetHealthAdvisor(
    PromptEngineMixin,
    BusinessLogicMixin,
    ConsultationMixin,
    ExtractionMixin,
    FallbackMixin,
    UtilsMixin
):
    """
    智能宠物健康顾问主类（Facade 模式）
    
    整合 LLM 能力与宠物档案数据，提供个性化的健康咨询服务。
    """
    
    def __init__(self):
        """初始化 AI 健康顾问（采用组合模式）"""
        try:
            self.client = ChatCompressClient()
            # 开启自动压缩，配合"先提取后压缩"策略使用
            self.client.auto_compress_enabled = True 
            logger.info("AI 健康顾问初始化成功 (医疗模式 - 自动压缩已启用)")
        except Exception as e:
            logger.error(f"AI 健康顾问初始化失败: {e}")
            raise


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("  AI 宠物健康顾问模块测试")
    print("=" * 60)
    
    try:
        advisor = PetHealthAdvisor()
        
        # 测试数据
        dog_profile = {
            "name": "小白",
            "species": "dog",
            "breed": "金毛犬",
            "age": 2,
            "weight": 25.5,
            "gender": "male",
            "recent_records": [
                {"date": "2026-04-15", "type": "checkup", "desc": "常规体检，体重正常"},
                {"date": "2026-03-10", "type": "illness", "desc": "感冒发烧，服药治疗"}
            ]
        }
        
        print("\n【测试1】喂养计划分析")
        print("-" * 60)
        feeding_advice = advisor.analyze_feeding_plan(dog_profile)
        print(feeding_advice)
        
        print("\n" + "=" * 60)
        print("  所有测试完成！✅")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
