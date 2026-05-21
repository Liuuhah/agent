"""
日志记录与文件管理 Mixin

职责：
- 将提取的 5W 信息、原始对话及失败记录持久化到本地文件
- 实现“兜底归档”策略，确保即使提取失败也能保存原始问诊记录
- 提供后台键盘监听功能，支持流式输出中断

依赖关系：
- ExtractorMixin: 接收提取结果并进行格式化保存
- ConfigManagerMixin: 获取 log_file_path 等路径配置

架构说明：
本模块位于继承链顶层。它不直接调用 LLM，而是作为整个系统的“记录员”，负责数据的最终落地。
"""
import os
import time
import sys
from datetime import datetime
from ._extractor import ExtractorMixin


class LoggerMixin(ExtractorMixin):
    """日志记录与文件管理 Mixin"""

    def _save_to_log_file(self, extracted_info, round_number, recent_messages=None, is_cumulative=False, counter_value=0, should_compress=False):
        """将提取的关键信息保存到日志文件"""
        log_dir = os.path.dirname(self.log_file_path)
        
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            extract_mode = "累积模式（包含历史对话）" if is_cumulative else "标准模式"
            
            log_content = "\n" + "=" * 60 + "\n"
            log_content += f"【记录时间】{current_time}\n"
            log_content += f"【对话轮次】第 {round_number} 轮\n"
            log_content += f"【提取模式】{extract_mode}\n"
            log_content += f"【计数器状态】extract_message_counter = {counter_value}\n"
            log_content += "=" * 60 + "\n\n"
            
            if extracted_info and "无法提取" not in extracted_info:
                log_content += "📊 5W 提取结果：\n"
                log_content += extracted_info.strip() + "\n\n"
                log_content += "✅ 提取状态：成功\n"
            else:
                log_content += "❌ 提取状态：失败\n"
                if extracted_info:
                    log_content += f"【失败原因】{extracted_info.strip()}\n"
                log_content += "\n"
            
            if recent_messages:
                log_content += f"\n📝 原始对话（最近 {len(recent_messages)} 条消息）：\n"
                for i, msg in enumerate(recent_messages, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    if role == 'tool':
                        summary = str(content)[:50] + "... [工具返回结果已截断]" if len(str(content)) > 200 else str(content).replace('\n', ' ').strip()
                    elif role == 'user' and isinstance(content, str) and '【宠物信息】' in content:
                        import re
                        symptom_match = re.search(r'【症状描述】\s*\n(.+)', content, re.DOTALL)
                        summary = symptom_match.group(1).strip() if symptom_match else content[-100:]
                    elif role == 'assistant' and isinstance(content, str):
                        summary = (content[:100].replace('\n', ' ').strip() + "...") if len(content) > 100 else content.replace('\n', ' ').strip()
                    else:
                        summary = str(content)[:100]
                    
                    log_content += f"[{i}] {role}: {summary}\n"
                log_content += "\n"
            
            log_content += f"💾 保存位置：{self.log_file_path}\n"
            log_content += f"🗜️ 后续操作：{'触发压缩' if should_compress else '未触发压缩'}\n"
            log_content += "=" * 60 + "\n"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_content)
            
            print(f"[日志保存] 成功保存到: {self.log_file_path}")
            return True
        except Exception as e:
            import traceback
            print(f"[日志保存] ❌ 保存失败: {e}")
            print(traceback.format_exc())
            return False

    def _save_short_consultation_record(self, reason, recent_messages, round_number=None):
        """兜底归档策略：保存简短问诊记录"""
        try:
            if round_number is None:
                round_number = len(self.chat_history) // 2
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_content = "\n" + "=" * 60 + "\n"
            log_content += f"【记录时间】{current_time}\n"
            log_content += f"【对话轮次】第 {round_number} 轮\n"
            log_content += f"【记录类型】📝 简短问诊记录（兜底归档）\n"
            log_content += f"【保存原因】{reason}\n"
            log_content += "=" * 60 + "\n\n"
            
            if recent_messages:
                log_content += f"💬 原始对话（共 {len(recent_messages)} 条消息）：\n\n"
                for i, msg in enumerate(recent_messages, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if role == 'assistant' and len(content) > 100:
                        summary = content[:100].replace('\n', ' ').strip() + "..."
                    else:
                        summary = content.replace('\n', ' ').strip() if isinstance(content, str) else str(content)
                    log_content += f"[{i}] {'AI助手' if role == 'assistant' else '用户'}: {summary}\n\n"
            else:
                log_content += "💬 无对话记录\n\n"
            
            log_content += f"💾 保存位置：{self.log_file_path}\n"
            log_content += "=" * 60 + "\n"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_content)
            
            print(f"[兜底归档] ✅ 已成功保存简短问诊记录到: {self.log_file_path}")
            return True
        except Exception as e:
            import traceback
            print(f"[兜底归档] ❌ 保存失败: {e}")
            print(traceback.format_exc())
            return False

    def _generate_dialogue_summary(self, recent_messages):
        """生成对话摘要（用于失败记录）"""
        try:
            user_msgs = [msg.get('content', '') for msg in recent_messages if msg.get('role') == 'user']
            ai_msgs = [msg.get('content', '') for msg in recent_messages if msg.get('role') == 'assistant']
            
            summary_parts = []
            if user_msgs: summary_parts.append(f"用户：{'、'.join(user_msgs[:3])}")
            if ai_msgs: summary_parts.append(f"AI：{'、'.join(ai_msgs[:3])}")
            
            summary = ' | '.join(summary_parts)
            return summary[:47] + "..." if len(summary) > 50 else summary
        except Exception as e:
            return f"生成摘要失败: {str(e)}"

    def _keyboard_listener(self):
        """后台键盘监听线程（守护线程），支持按 Esc 中断输出"""
        if sys.platform != 'win32':
            return
        
        try:
            import msvcrt
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if ord(key) == 27:
                        self.is_interrupted = True
                        break
                time.sleep(0.05)
        except Exception:
            pass
