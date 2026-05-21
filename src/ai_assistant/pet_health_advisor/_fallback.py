"""
模块名称：_fallback.py
职责：当 LLM 不可用时，提供基于规则的备选建议
依赖：无
被依赖：_business_logic.py

核心方法：
- _fallback_feeding_advice(): 基于规则的喂养建议
- _fallback_diagnosis_advice(): 基于规则的诊断建议
"""

from typing import Dict, Any


class FallbackMixin:
    """降级策略混入类"""
    
    def _fallback_feeding_advice(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        降级策略：基于规则的喂养建议（当 LLM 不可用时）
        
        设计原则：
        - 保证基本可用性 → 用户体验不中断
        - 简单规则引擎 → 覆盖常见场景
        
        Args:
            pet_profile_dict: 宠物档案字典
        
        Returns:
            str: 基于规则的喂养建议
        """
        name = pet_profile_dict.get("name", "宠物")
        species = pet_profile_dict.get("species", "unknown")
        age = pet_profile_dict.get("age", 0)
        weight = pet_profile_dict.get("weight", 0)
        
        advice = f"【{name} 的喂养建议（基础版）】\n\n"
        
        if species == "dog":
            if age < 1:
                advice += f"- 幼犬期：每日喂食 3-4 次，每次约 {weight * 20:.0f}g 幼犬粮\n"
                advice += "- 选择高蛋白、易消化的幼犬专用粮\n"
            elif age < 7:
                advice += f"- 成犬期：每日喂食 2 次，每次约 {weight * 15:.0f}g 成犬粮\n"
                advice += "- 保持均衡营养，适量添加肉类和蔬菜\n"
            else:
                advice += f"- 老年犬：每日喂食 2 次，每次约 {weight * 12:.0f}g 老年犬粮\n"
                advice += "- 选择低脂、易消化的配方，关注关节健康\n"
        elif species == "cat":
            if age < 1:
                advice += f"- 幼猫期：每日喂食 4-5 次，每次约 {weight * 25:.0f}g 幼猫粮\n"
                advice += "- 保证充足饮水，选择高蛋白猫粮\n"
            elif age < 7:
                advice += f"- 成猫期：每日喂食 2-3 次，每次约 {weight * 20:.0f}g 成猫粮\n"
                advice += "- 干湿搭配，预防泌尿系统疾病\n"
            else:
                advice += f"- 老年猫：每日喂食 2-3 次，每次约 {weight * 18:.0f}g 老年猫粮\n"
                advice += "- 关注肾脏健康，选择低磷配方\n"
        else:
            advice += "- 请咨询专业兽医获取个性化喂养建议\n"
        
        advice += "\n⚠️ 注意：以上为基础建议，具体情况请咨询兽医或宠物营养师。"
        
        return advice
    
    def _fallback_diagnosis_advice(self, symptoms: str) -> str:
        """
        降级策略：基于规则的诊断建议
        
        Args:
            symptoms: 症状描述
        
        Returns:
            str: 通用诊断建议
        """
        advice = "【症状初步分析（基础版）】\n\n"
        advice += "⚠️ 本建议仅供参考，不能替代专业兽医诊断。\n\n"
        
        # 关键词匹配（简单规则引擎）
        urgent_keywords = ["昏迷", "抽搐", "呼吸困难", "大量出血", "中毒"]
        warning_keywords = ["呕吐", "腹泻", "发烧", "不吃东西", "精神萎靡"]
        
        if any(keyword in symptoms for keyword in urgent_keywords):
            advice += "🔴 **紧急程度：高**\n"
            advice += "您的宠物出现严重症状，建议**立即前往宠物医院**！\n\n"
        elif any(keyword in symptoms for keyword in warning_keywords):
            advice += "🟡 **紧急程度：中**\n"
            advice += "建议尽快（24 小时内）带宠物就医检查。\n\n"
        else:
            advice += "🟢 **紧急程度：低**\n"
            advice += "可以先观察 1-2 天，如症状持续或加重再就医。\n\n"
        
        advice += "【家庭护理建议】\n"
        advice += "1. 保持环境安静舒适\n"
        advice += "2. 提供充足的清洁饮水\n"
        advice += "3. 暂时减少活动量，让宠物休息\n"
        advice += "4. 记录症状变化（频率、严重程度）\n\n"
        
        advice += "【何时就医】\n"
        advice += "- 症状持续超过 24 小时\n"
        advice += "- 症状明显加重\n"
        advice += "- 出现新的症状\n"
        advice += "- 宠物精神状态明显变差"
        
        return advice
