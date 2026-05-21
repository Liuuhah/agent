"""
兼容层：从子包导入主类

注意：此文件仅用于保持向后兼容，新代码应直接使用：
    from ai_assistant.pet_health_advisor.main import PetHealthAdvisor
或
    from ai_assistant.pet_health_advisor import PetHealthAdvisor
"""

from .pet_health_advisor.main import PetHealthAdvisor

__all__ = ['PetHealthAdvisor']
