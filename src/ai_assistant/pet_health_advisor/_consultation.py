"""
模块名称：_consultation.py
职责：实现闲聊/问诊双模态交互
依赖：_business_logic（间接）
被依赖：无

核心方法：
- _detect_intent(): 意图识别
- consult(): 统一咨询接口
- compress_memory(): 手动触发记忆压缩
- get_medical_summary(): 获取对话摘要
"""

import logging

logger = logging.getLogger('PetHealthAdvisor')


class ConsultationMixin:
    """双模态咨询混入类"""
    
    def _detect_intent(self, user_input: str) -> str:
        """
        简单的关键词意图识别。
        返回 'chat' (闲聊) 或 'consult' (问诊)。
        """
        # 医疗关键词列表
        medical_keywords = [
            "病", "痛", "吐", "拉", "吃", "喝", "药", "医", "诊", "症状",
            "发烧", "咳嗽", "瘦", "胖", "呕吐", "腹泻", "精神", "异常",
            "不吃", "不喝", "拉肚子", "感冒", "受伤", "流血", "抽搐"
        ]
        
        # 如果包含任何医疗关键词，则进入专业模式
        if any(kw in user_input for kw in medical_keywords):
            return "consult"
        
        return "chat"
    
    def consult(self, user_input: str) -> str:
        """统一的咨询接口，支持双模态交互"""
        # 1. 意图识别
        intent = self._detect_intent(user_input)
        
        if intent == "chat":
            # 闲聊模式：注入轻松的指令
            context_instruction = "\n\n【当前状态：闲聊模式】\n用户只是在打招呼或闲聊。请保持轻松、随和的语气，像朋友一样简短回应，不要输出任何医疗建议格式。可以适当使用表情符号让对话更亲切。"
            temperature = 0.8
            logger.info("进入闲聊模式")
        else:
            # 专业模式：注入严谨的指令
            context_instruction = "\n\n【当前状态：专业问诊模式】\n用户提到了健康问题。请严格按照兽医标准，提供结构化诊断、护理建议和紧急程度评估。语气要专业且温和。"
            temperature = 0.4
            logger.info("进入专业问诊模式")
        
        # 2. 更新 System Prompt（追加动态指令）
        original_system_prompt = self.client.system_prompt
        self.client.system_prompt = original_system_prompt + context_instruction
        
        # 3. 调用 LLM
        try:
            response, time_taken = self.client.send_request_stream(
                user_input,
                max_tokens=1024,
                temperature=temperature
            )
            
            if not response:
                raise RuntimeError("LLM 未返回有效内容")
            
            # 记录到历史对话中
            self.client.add_to_history('user', user_input)
            self.client.add_to_history('assistant', response)
            
            logger.info(f"咨询完成（{intent}模式），耗时 {time_taken:.2f} 秒")
            
            # 触发自动提取检查
            try:
                self.client._check_and_extract_key_info()
            except Exception as e:
                # 静默失败，不影响主对话流程
                logger.warning(f"自动提取检查异常: {e}")
            
            # 恢复原始 System Prompt
            self.client.system_prompt = original_system_prompt
            
            return response
            
        except Exception as e:
            logger.error(f"咨询失败: {e}")
            # 恢复原始 System Prompt
            self.client.system_prompt = original_system_prompt
            return f"抱歉，我暂时无法回应。错误信息：{str(e)}"
    
    def compress_memory(self):
        """手动触发记忆压缩（医疗模式下使用）"""
        self.client._compress_chat_history()
        logger.info("已执行手动记忆压缩")

    def get_medical_summary(self, force=False):
        """获取当前的 AI 管家对话摘要（5W 信息提取）"""
        if force:
            return self.client.extract_summary_now()
        else:
            # 默认行为：仅返回已有的或触发常规检查
            self.client._check_and_extract_key_info()
            return "已触发常规检查，若满足条件将自动归档。"
