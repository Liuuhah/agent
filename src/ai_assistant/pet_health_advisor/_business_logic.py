"""
模块名称：_business_logic.py
职责：实现喂养计划分析、症状诊断、健康报告生成等核心业务逻辑
依赖：_prompt_engine, _fallback, _utils
被依赖：_consultation

核心方法：
- set_current_pet_context(): 设置宠物上下文
- reset_context(): 重置上下文
- analyze_feeding_plan(): 分析喂养计划
- diagnose_symptoms(): 诊断症状
- generate_health_report(): 生成健康报告
"""

import logging
from typing import Dict, Any

logger = logging.getLogger('PetHealthAdvisor')


class BusinessLogicMixin:
    """核心业务逻辑混入类"""
    
    def set_current_pet_context(self, pet_data: dict):
        """
        设置当前咨询宠物的上下文信息到 System Prompt 中。
        
        Args:
            pet_data: 包含 name, species, breed, age, weight, gender, recent_records 的字典。
        """
        context_info = f"""
【当前咨询对象档案】
- 姓名：{pet_data.get('name', '未知')}
- 物种：{pet_data.get('species', 'unknown')}
- 品种：{pet_data.get('breed', '未知品种')}
- 年龄：{pet_data.get('age', 0)} 岁
- 体重：{pet_data.get('weight', 0)} kg
- 性别：{'公' if pet_data.get('gender') == 'male' else '母' if pet_data.get('gender') == 'female' else '未知'}
- 近期健康记录：{str(pet_data.get('recent_records', []))}

【重要指令】
1. 你已经知晓上述宠物的所有基本信息，无需再次向用户确认。
2. 请基于这些信息进行诊断和建议。
3. 如果用户提到的症状与档案不符，请以用户最新描述为准。
4. 在回答时可以直接称呼宠物的名字，让对话更亲切自然。
"""
        
        # 调用底层接口更新 System Prompt
        self.client.set_system_prompt(context_info)
        logger.info(f"已为宠物 {pet_data.get('name')} 注入上下文信息")
    
    def reset_context(self):
        """重置上下文信息（用于切换宠物或退出咨询模式）"""
        self.client.reset_system_prompt()
        self.client.clear_history()
        logger.info("已重置 AI 管家上下文")
    
    def analyze_feeding_plan(self, pet_profile_dict: Dict[str, Any]) -> str:
        """分析并生成个性化喂养计划"""
        # 数据校验
        self._validate_pet_profile(pet_profile_dict, required_fields=["name", "species", "age", "weight"])
        
        # 构建 LLM Prompt
        prompt = self._build_feeding_plan_prompt(pet_profile_dict)
        
        # 调用 LLM
        try:
            logger.info(f"开始分析 {pet_profile_dict['name']} 的喂养计划...")
            response, time_taken = self.client.send_request_stream(prompt, max_tokens=1024)
            
            if not response:
                raise RuntimeError("LLM 未返回有效内容")
            
            # 记录到历史对话中
            self.client.add_to_history('user', prompt)
            self.client.add_to_history('assistant', response)
            
            logger.info(f"喂养计划分析完成，耗时 {time_taken:.2f} 秒")
            return response
            
        except Exception as e:
            logger.error(f"喂养计划分析失败: {e}")
            # 降级策略：返回规则引擎建议
            return self._fallback_feeding_advice(pet_profile_dict)
    
    def diagnose_symptoms(self, pet_profile_dict: Dict[str, Any], symptoms: str) -> str:
        """根据症状描述进行初步诊断"""
        # 数据校验
        if not symptoms or not symptoms.strip():
            raise ValueError("症状描述不能为空")
        
        self._validate_pet_profile(pet_profile_dict, required_fields=["name", "species", "age"])
        
        # 构建 LLM Prompt
        prompt = self._build_diagnosis_prompt(pet_profile_dict, symptoms)
        
        # 调用 LLM
        try:
            logger.info(f"开始诊断 {pet_profile_dict['name']} 的症状...")
            response, time_taken = self.client.send_request_stream(prompt, max_tokens=1024)
            
            if not response:
                raise RuntimeError("LLM 未返回有效内容")
            
            # 记录到历史对话中
            self.client.add_to_history('user', prompt)
            self.client.add_to_history('assistant', response)
            
            logger.info(f"症状诊断完成，耗时 {time_taken:.2f} 秒")
            return response
            
        except Exception as e:
            logger.error(f"症状诊断失败: {e}")
            # 降级策略：返回通用建议
            return self._fallback_diagnosis_advice(symptoms)
    
    def generate_health_report(self, pet_profile_dict: Dict[str, Any]) -> str:
        """生成综合健康报告"""
        # 数据校验
        self._validate_pet_profile(pet_profile_dict, required_fields=["name", "species"])
        
        if "recent_records" not in pet_profile_dict:
            pet_profile_dict["recent_records"] = []
        
        # 构建 LLM Prompt
        prompt = self._build_health_report_prompt(pet_profile_dict)
        
        # 调用 LLM
        try:
            logger.info(f"开始生成 {pet_profile_dict['name']} 的健康报告...")
            response, time_taken = self.client.send_request_stream(prompt, max_tokens=2048)
            
            if not response:
                raise RuntimeError("LLM 未返回有效内容")
            
            logger.info(f"健康报告生成完成，耗时 {time_taken:.2f} 秒")
            return response
            
        except Exception as e:
            logger.error(f"健康报告生成失败: {e}")
            return f"抱歉，暂时无法生成健康报告。错误信息：{str(e)}"
