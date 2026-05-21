"""
模块名称：_utils.py
职责：提供数据校验和格式化功能
依赖：无
被依赖：_business_logic.py

核心方法：
- _validate_pet_profile(): 校验宠物档案必要字段
- format_pet_profile_for_llm(): 格式化为 LLM 友好字符串
"""

from typing import Dict, List, Any


class UtilsMixin:
    """工具方法混入类"""
    
    def _validate_pet_profile(self, pet_profile_dict: Dict[str, Any], required_fields: List[str]):
        """
        校验宠物档案字典的必要字段
        
        设计原则：
        - 早期失败 → 快速发现数据问题
        - 清晰错误信息 → 便于调试
        
        Args:
            pet_profile_dict: 宠物档案字典
            required_fields: 必需字段列表
        
        Raises:
            ValueError: 如果缺少必要字段
        """
        missing_fields = [field for field in required_fields if field not in pet_profile_dict]
        if missing_fields:
            raise ValueError(f"宠物档案缺少必要字段: {', '.join(missing_fields)}")
    
    def format_pet_profile_for_llm(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        将宠物档案字典格式化为 LLM 友好的字符串
        
        设计原则：
        - 简洁明了 → 节省 Token
        - 结构化 → 便于 LLM 理解
        
        Args:
            pet_profile_dict: 宠物档案字典
        
        Returns:
            str: 格式化的字符串
        """
        lines = [
            f"名字: {pet_profile_dict.get('name', '未知')}",
            f"物种: {pet_profile_dict.get('species', 'unknown')}",
            f"品种: {pet_profile_dict.get('breed', '未知')}",
            f"年龄: {pet_profile_dict.get('age', 0)} 岁",
            f"体重: {pet_profile_dict.get('weight', 0)} kg",
            f"性别: {pet_profile_dict.get('gender', 'unknown')}"
        ]
        
        return "\n".join(lines)
