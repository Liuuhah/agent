"""
医疗信息提取与康复建议模块

职责：
- API-002: 从 OCR 文本中提取结构化医疗数据
- API-003: 生成个性化康复与饮食建议
"""

import json
import requests
from ai_assistant.pet_health_advisor import PetHealthAdvisor


class MedicalInfoExtractor:
    """医疗信息提取器"""

    def __init__(self, advisor: PetHealthAdvisor):
        self.advisor = advisor
        # 获取客户端配置信息用于直接发送请求
        self.client = advisor.client

    def _send_sync_request(self, prompt: str) -> str:
        """
        发送同步请求到 LLM（非流式）
        
        Args:
            prompt: 提示词
            
        Returns:
            str: LLM 返回的完整响应
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.client.token}"
        }
        
        payload = {
            "model": self.client.model,
            "messages": [
                {"role": "system", "content": "你是一位专业的兽医助手。"},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "max_tokens": 2048,
            "temperature": 0.3,
            "reasoning_effort": "low",
            "thinking": {"type": "disabled"}
        }
        
        api_url = f"{self.client.base_url}/chat/completions"
        
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=600)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            raise RuntimeError("LLM API 请求超时，请检查网络连接或稍后重试（已设置 600 秒超时）")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM API 请求失败: {e}")
        except Exception as e:
            raise RuntimeError(f"信息提取失败: {e}")

    def extract_structured_info(self, raw_text: str) -> dict:
        """
        API-002: 提取结构化医疗信息
        
        Args:
            raw_text: OCR 识别出的原始文本
            
        Returns:
            dict: 包含 diagnosis, medicines, follow_up_date 等的字典
        """
        prompt = f"""
        你是一位专业的兽医助手。请从以下医疗文本中提取关键信息，并严格以 JSON 格式返回。
        
        文本可能包含以下类型：
        1. 血常规/化验单：包含各项血液指标、数值、参考范围、异常标记
        2. 诊断病历：包含诊断结论、处方药品、医嘱等
        
        需要提取的字段：
        - document_type (str): 文档类型（"blood_test" 或 "diagnosis"）
        - pet_info (dict): 宠物信息（如果有），包含 name, breed, age, weight 等
        - test_results (list): 化验指标列表（仅当 document_type 为 blood_test 时），每个元素包含 name (指标名), value (结果值), unit (单位), lower_limit (下限), upper_limit (上限), abnormal (是否异常: true/false)
        - diagnosis (str): 诊断结论（仅当 document_type 为 diagnosis 时）
        - medicines (list): 药品列表（仅当 document_type 为 diagnosis 时），每个元素包含 name (药名), dose (剂量/规格), freq (用法用量)
        - follow_up_date (str): 复诊日期 (YYYY-MM-DD)，如果没有则为 null
        - doctor_advice (str): 医生的额外医嘱或检验员的备注
        
        医疗文本：
        {raw_text}
        
        JSON 输出：
        """
        
        try:
            response = self._send_sync_request(prompt)
            # 尝试清理 LLM 可能返回的 Markdown 标记
            clean_response = response.replace("```json", "").replace("```", "").strip()
            extracted_data = json.loads(clean_response)
            return extracted_data
        except Exception as e:
            raise RuntimeError(f"Information extraction failed: {e}")

    def generate_recovery_advice(self, pet_id: str, diagnosis: str, medicines: list) -> str:
        """
        API-003: 生成康复与饮食建议
        
        Args:
            pet_id: 宠物 ID
            diagnosis: 诊断结论
            medicines: 药品列表
            
        Returns:
            str: 康复建议文本
        """
        # 1. 获取宠物档案以注入上下文
        from modules.pet_profile_manager import SmartPetProfileSystem
        system = SmartPetProfileSystem()
        pet = system.profile_manager.get_pet(pet_id)
        
        if not pet:
            raise ValueError(f"Pet with ID {pet_id} not found.")

        # 2. 构造 Prompt
        context = f"宠物姓名: {pet.name}, 物种: {pet.species}, 年龄: {pet.age}岁, 体重: {pet.weight}kg"
        prompt = f"""
        基于以下宠物信息和诊断结果，生成一份温暖、通俗易懂的康复指南。
        
        宠物信息: {context}
        诊断结果: {diagnosis}
        使用药品: {medicines}
        
        请包含以下内容：
        1. 饮食调整建议 (diet_plan)
        2. 日常护理要点 (care_tips)
        3. 需要警惕的异常反应 (warning_signs)
        
        语气要像一位贴心的兽医朋友。
        """
        
        return self._send_sync_request(prompt)
