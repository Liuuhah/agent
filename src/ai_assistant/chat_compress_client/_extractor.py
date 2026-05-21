"""
5W信息提取与归档 Mixin

职责：
- 构建 5W (Who, What, When, Where, Why) 提取提示词
- 发送提取请求并解析 LLM 返回的结构化信息
- 管理累积式提取计数器，实现周期性自动归档

依赖关系：
- CompressorMixin: 遵循“先提取后压缩”逻辑，在提取成功后触发压缩
- ChatCoreMixin: 需要调用底层通信方法发送提取请求

架构说明：
本模块负责智能信息的抽取。它依赖于中层的压缩逻辑来确保在归档后才进行上下文清理。
"""
import json
import http.client
import re
from ._compressor import CompressorMixin


class ExtractorMixin(CompressorMixin):
    """5W信息提取与归档 Mixin"""

    def _check_and_extract_key_info(self):
        """检查是否需要提取关键信息，并在满足条件时执行"""
        if not self.auto_extract_enabled: return
        
        if self.skip_next_extract:
            self.skip_next_extract = False
            print("[关键信息提取] 用户跳过本次提取")
            return
        
        rounds = len(self.chat_history) // 2
        current_user_msgs = sum(1 for msg in self.chat_history if msg.get('role') == 'user')
        
        if current_user_msgs > self.extract_message_counter:
            self.extract_message_counter = current_user_msgs
        
        if rounds > 0 and rounds % self.extract_interval == 0:
            if self.extract_message_counter >= self.extract_interval or rounds == self.extract_interval:
                print(f"\n[关键信息提取] 检测到第{rounds}轮对话，开始提取关键信息...")
                self._extract_5w_info()

    def _extract_5w_info(self, messages=None):
        """执行 5W 关键信息提取（支持累积模式和自定义消息列表）"""
        if messages is not None:
            recent_messages = messages
            is_cumulative = False
        else:
            recent_messages = self.chat_history[-(self.extract_interval * 2):]
            is_cumulative = (self.extract_message_counter > self.extract_interval)
        
        extract_prompt = self._build_extract_prompt(recent_messages, is_cumulative)
        
        print("[关键信息提取] 正在调用 LLM...")
        response_data = self._send_extract_request(extract_prompt, max_tokens=4096, temperature=0.5)
        
        extracted_info, status, reason = self._parse_extraction_response(response_data)
        
        if status == "success":
            old_counter = self.extract_message_counter
            self.extract_message_counter = 0
            
            should_compress = self._should_compress()
            success = self._save_to_log_file(
                extracted_info=extracted_info,
                round_number=len(self.chat_history) // 2,
                recent_messages=recent_messages,
                is_cumulative=is_cumulative,
                counter_value=old_counter,
                should_compress=should_compress
            )
            
            if success and should_compress:
                print("\n[协同清理] 归档成功，开始执行上下文压缩...")
                self._compress_chat_history()
        
        elif status in ["insufficient_info", "technical_error", "format_error"]:
            self._save_short_consultation_record(
                reason=f"自动提取失败: {reason}",
                recent_messages=recent_messages,
                round_number=len(self.chat_history) // 2
            )

    def _build_extract_prompt(self, recent_messages, is_cumulative=False):
        """构建 5W 信息提取的提示词"""
        conversation_text = ""
        for i, msg in enumerate(recent_messages, 1):
            role = "用户" if msg['role'] == 'user' else "AI助手"
            content = msg.get('content', '')
            if isinstance(content, list): content = str(content)
            conversation_text += f"{i}. {role}: {content}\n"
        
        if is_cumulative:
            half_count = len(recent_messages) // 2
            historical_text = conversation_text.split('\n')[:half_count]
            current_text = '\n'.join(conversation_text.split('\n')[half_count:])
            
            prompt = f"""请分析以下对话内容，分为两个部分处理。
【第一部分：历史对话摘要】
{'\n'.join(historical_text)}

【第二部分：当前对话 5W 提取】
{current_text}

【处理规则】
1. **对第一部分**：用 1-2 句话简要总结这部分对话的核心内容。
2. **对第二部分**：按照 5W 规则提取关键信息。如果信息太少，输出：【无法提取】对话内容可提取的信息太少

【最终输出格式】
=== 历史对话摘要 ===
[这里写 1-2 句话的历史对话总结]

=== 当前对话 5W 信息 ===
- Who: [参与者姓名或角色]
- What: [主要事件或话题]
- When: [时间]
- Where: [地点]
- Why: [原因或目的]

【开始提取】"""
        else:
            prompt = f"""请分析以下对话内容，按照 5W 规则提取关键信息。
【对话内容】
{conversation_text}

【提取规则】
如果可以提取，请严格按照以下格式输出：
- Who: [参与者姓名或角色]
- What: [主要事件或话题]
- When: [时间]
- Where: [地点]
- Why: [原因或目的]

如果对话只是问候、闲聊、或信息太少，请输出：
【无法提取】对话内容可提取的信息太少，没有值得提取的关键信息

【开始提取】"""
        return prompt

    def _send_extract_request(self, prompt, max_tokens=256, temperature=0.3):
        """发送提取请求到 LLM"""
        try:
            conn = http.client.HTTPSConnection(self.host) if self.base_url.startswith('https://') else http.client.HTTPConnection(self.host)
            headers = {'Content-Type': 'application/json'}
            if self.token: headers['Authorization'] = f'Bearer {self.token}'
            
            data = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的信息提取助手。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': temperature,
                'stream': False
            }
            
            conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
            response = conn.getresponse()
            response_data = json.loads(response.read().decode())
            conn.close()
            return response_data
        except Exception as e:
            print(f"[提取请求错误] {str(e)}")
            return None

    def _parse_extraction_response(self, response_data):
        """解析 LLM 返回的提取结果"""
        if response_data is None:
            return None, "technical_error", "API 调用失败"
        
        if 'choices' not in response_data or len(response_data['choices']) == 0:
            return None, "technical_error", "LLM 返回空响应"
        
        choice = response_data['choices'][0]
        message = choice.get('message', {})
        content = message.get('content', '').strip()
        
        if not content:
            reasoning_content = message.get('reasoning_content', '')
            if reasoning_content:
                who_match = re.search(r'-\s*Who:', reasoning_content)
                if who_match: content = reasoning_content[who_match.start():].strip()
        
        if not content:
            return None, "technical_error", "LLM 返回空内容"
        
        # 检查累积模式格式
        if '=== 历史对话摘要 ===' in content and '=== 当前对话 5W 信息 ===' in content:
            five_w_section = content.split('=== 当前对话 5W 信息 ===')[1].strip()
            if '【无法提取】' in five_w_section:
                return None, "insufficient_info", "当前对话内容可提取的信息太少"
            if any(kw in five_w_section for kw in ['Who', 'What']):
                return content, "success", None
            return None, "format_error", "5W 部分不符合格式要求"
        
        # 检查标准模式
        if "【无法提取】" in content:
            return None, "insufficient_info", "对话内容无法提取"
        
        if not any(kw in content for kw in ['Who', 'What']):
            return None, "insufficient_info", "返回内容过短或格式不符"
        
        if content.count("未提及") >= 4:
            return None, "insufficient_info", "对话内容可提取的信息太少"
        
        return content, "success", None

    def extract_summary_now(self):
        """强制立即提取当前对话摘要"""
        print("\n[强制提取] 正在调用 LLM 进行 5W 信息提取...")
        if len(self.chat_history) < 2:
            self._save_short_consultation_record(reason="暂无对话记录", recent_messages=[])
            return "已成功保存问诊记录至日志文件（当前无对话内容）。"
        
        recent_messages = self.chat_history[-10:]
        extract_prompt = self._build_extract_prompt(recent_messages, is_cumulative=False)
        response_data = self._send_extract_request(extract_prompt, max_tokens=4096, temperature=0.5)
        extracted_info, status, reason = self._parse_extraction_response(response_data)
        
        if status == "success":
            success = self._save_to_log_file(
                extracted_info=extracted_info,
                round_number=len(self.chat_history) // 2,
                recent_messages=recent_messages,
                is_cumulative=False,
                counter_value=self.extract_message_counter,
                should_compress=self._should_compress()
            )
            return "已成功提取本次问诊精华，并保存至 D:\\chat-log 目录。" if success else "提取成功但保存失败。"
        else:
            self._save_short_consultation_record(reason=reason, recent_messages=recent_messages)
            return "已成功保存本次问诊记录至 D:\\chat-log 目录（原始对话备份）。"

    def _show_extract_settings(self):
        """显示关键信息提取相关设置"""
        print("\n[关键信息提取设置]")
        print(f"  自动提取: {'✅ 启用' if self.auto_extract_enabled else '❌ 禁用'}")
        print(f"  下次跳过: {'是' if self.skip_next_extract else '否'}")
        print(f"  提取频率: 每 {self.extract_interval} 轮对话")
        print(f"  日志路径: {self.log_file_path}")
        print()
