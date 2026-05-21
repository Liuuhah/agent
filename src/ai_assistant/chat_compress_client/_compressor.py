"""
对话压缩逻辑 Mixin

职责：
- 监控对话轮数与上下文长度，判断是否触发压缩
- 调用 LLM 对历史对话进行摘要总结
- 执行“先提取后压缩”的协同清理逻辑

依赖关系：
- ChatCoreMixin: 需要发送总结请求到 LLM
- ConfigManagerMixin: 获取 max_rounds, compress_ratio 等阈值配置

架构说明：
本模块位于继承链中层。它利用底层通信能力实现记忆管理，并为上层归档提供触发时机。
"""
import json
import http.client
from ._chat_core import ChatCoreMixin


class CompressorMixin(ChatCoreMixin):
    """对话压缩逻辑 Mixin"""

    def _should_compress(self):
        """检查是否需要压缩聊天记录"""
        if not self.auto_compress_enabled:
            return False
        
        if self.skip_next_compress:
            self.skip_next_compress = False
            print("\n[压缩跳过] 用户选择跳过本次压缩")
            return False
        
        rounds = self._count_rounds()
        context_tokens = sum(self._estimate_tokens(msg.get('content', '')) for msg in self.chat_history if 'content' in msg)
        
        should_compress_by_rounds = rounds > self.max_rounds
        should_compress_by_tokens = context_tokens > self.max_context_tokens
        
        if should_compress_by_rounds or should_compress_by_tokens:
            reason = []
            if should_compress_by_rounds: reason.append(f"对话轮数({rounds})超过限制({self.max_rounds})")
            if should_compress_by_tokens: reason.append(f"上下文长度({context_tokens} tokens)超过限制({self.max_context_tokens} tokens)")
            print(f"\n[压缩触发] {'; '.join(reason)}")
            return True
        return False

    def _compress_chat_history(self):
        """压缩聊天历史记录：前70%内容进行LLM总结，后30%保留原文"""
        if len(self.chat_history) < 3:
            print("[压缩跳过] 聊天记录太少，无需压缩")
            return
        
        total_messages = len(self.chat_history)
        compress_count = int(total_messages * self.compress_ratio)
        keep_count = total_messages - compress_count
        
        if keep_count < 2:
            keep_count = 2
            compress_count = total_messages - keep_count
        
        print(f"[压缩开始] 总共{total_messages}条消息，压缩前{compress_count}条，保留后{keep_count}条")
        
        messages_to_compress = self.chat_history[:compress_count]
        messages_to_keep = self.chat_history[compress_count:]
        
        compress_text = ""
        for msg in messages_to_compress:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if isinstance(content, dict): content = json.dumps(content, ensure_ascii=False)
            compress_text += f"{role}: {content}\n\n"
        
        print("[压缩中] 正在调用LLM总结历史对话...")
        summary = self._summarize_conversation(compress_text)
        
        if summary:
            compressed_message = {
                'role': 'user',
                'content': f"【之前的对话摘要】\n{summary}\n\n请基于以上背景继续对话。"
            }
            self.chat_history = [compressed_message] + messages_to_keep
            print(f"[压缩完成] 从{total_messages}条消息压缩为{len(self.chat_history)}条消息")
        else:
            print("[压缩失败] LLM总结失败，保持原聊天记录")

    def _summarize_conversation(self, conversation_text):
        """调用LLM对对话内容进行总结"""
        try:
            conn = http.client.HTTPSConnection(self.host) if self.base_url.startswith('https://') else http.client.HTTPConnection(self.host)
            
            headers = {'Content-Type': 'application/json'}
            if self.token: headers['Authorization'] = f'Bearer {self.token}'
            
            prompt = f"""请对以下对话历史进行简洁的总结，提取关键信息和上下文。
要求：1. 用中文输出总结 2. 控制在200字以内 3. 包含用户的主要信息和问题 4. 直接输出总结内容

对话历史：
{conversation_text}

总结："""
            
            data = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的对话总结助手。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 512,
                'temperature': 0.3,
                'stream': False
            }
            
            conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
            response = conn.getresponse()
            response_data = json.loads(response.read().decode())
            conn.close()
            
            if 'error' in response_data: return None
            
            message = response_data['choices'][0].get('message', {})
            summary = message.get('content', '').strip()
            
            if not summary and message.get('reasoning_content'):
                # 尝试从 reasoning_content 提取
                import re
                draft_match = re.search(r'4\.\s*\*\*Drafting the Summary.*?:\s*(.+)', message['reasoning_content'], re.DOTALL)
                if draft_match: summary = draft_match.group(1).strip()
            
            return summary if summary else None
        except Exception as e:
            print(f"[调试] 总结过程出现异常: {e}")
            return None

    def _show_compress_settings(self):
        """显示压缩相关设置"""
        print("\n[压缩设置]")
        print(f"  自动压缩: {'✅ 启用' if self.auto_compress_enabled else '❌ 禁用'}")
        print(f"  下次跳过: {'是' if self.skip_next_compress else '否'}")
        print(f"  轮数阈值: {self.max_rounds} 轮")
        print(f"\n[可用命令]")
        print(f"  skip_compress / 跳过压缩  - 跳过下次自动压缩")
        print(f"  enable_compress / 启用压缩 - 启用自动压缩")
        print(f"  disable_compress / 禁用压缩 - 禁用自动压缩")
        print(f"  compress_settings / 压缩设置 - 显示此信息")
        print()
