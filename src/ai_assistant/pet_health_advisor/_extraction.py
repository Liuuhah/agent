"""
模块名称：_extraction.py
职责：处理对话历史提取、轮次解析、摘要归档
依赖：无（直接操作 self.client）
被依赖：无

核心方法：
- get_history_display(): 生成带轮次标记的历史记录
- extract_summary_by_rounds(): 根据轮次表达式提取摘要
- _parse_round_numbers(): 解析轮次表达式
- _build_temp_context(): 构建临时上下文
"""

import logging
from typing import List, Tuple

logger = logging.getLogger('PetHealthAdvisor')


class ExtractionMixin:
    """精准提取混入类"""
    
    def get_history_display(self) -> str:
        """
        生成带轮次标记的历史记录字符串，用于 /list 指令。
        
        Returns:
            str: 格式化的历史记录文本
        """
        if not self.client.chat_history:
            return "暂无对话历史。"
        
        display = ""
        round_num = 1
        i = 0
        
        while i < len(self.client.chat_history):
            msg = self.client.chat_history[i]
            
            # 查找 user 消息
            if msg.get('role') == 'user':
                user_content = msg.get('content', '')
                assistant_content = ''
                
                # 查找对应的 assistant 回复
                if i + 1 < len(self.client.chat_history) and self.client.chat_history[i + 1].get('role') == 'assistant':
                    assistant_content = self.client.chat_history[i + 1].get('content', '')
                    i += 2  # 跳过两条消息
                else:
                    i += 1  # 只有一条 user 消息
                
                # 截断过长的内容以便显示
                if len(user_content) > 100:
                    user_content = user_content[:97] + "..."
                if len(assistant_content) > 100:
                    assistant_content = assistant_content[:97] + "..."
                
                display += f"--- Round {round_num} ---\n"
                display += f"[你]: {user_content}\n"
                if assistant_content:
                    display += f"[AI]: {assistant_content}\n"
                display += "\n"
                round_num += 1
            else:
                i += 1
        
        if not display:
            return "暂无完整的对话轮次。"
        
        return display

    def extract_summary_by_rounds(self, round_expression: str) -> str:
        """
        根据用户输入的表达式（如 '1,3-5'）提取指定轮次的摘要。
        
        Args:
            round_expression: 轮次表达式，支持以下格式：
                - 离散选择：'1,3,5'
                - 范围选择：'1-3'
                - 混合选择：'1,3-5,8'
        
        Returns:
            str: 提取结果或错误提示
        """
        try:
            # 1. 解析轮次表达式
            round_numbers = self._parse_round_numbers(round_expression)
            
            if not round_numbers:
                return "[系统] 无法识别您的指令，请使用格式：/archive 1,3-5"
            
            # 2. 检查是否有非法数字（<=0）
            invalid_rounds = [r for r in round_numbers if r <= 0]
            if invalid_rounds:
                return f"[系统] 轮次必须为正整数，检测到无效轮次：{invalid_rounds}"
            
            # 3. 构建临时上下文
            temp_messages, warnings = self._build_temp_context(round_numbers)
            
            if not temp_messages:
                return f"[系统] 未找到有效的对话轮次。{warnings}"
            
            # 4. 调用底层 LLM 进行总结
            print(f"\n[精准提取] 正在提取第 {round_numbers} 轮对话...")
            self.client._extract_5w_info(messages=temp_messages)
            
            # 5. 返回结果
            warning_msg = f"\n注意：{warnings}" if warnings else ""
            return f"[系统] 已成功提取第 {', '.join(map(str, round_numbers))} 轮对话精华，并保存至 D:\\chat-log{warning_msg}。"
            
        except Exception as e:
            logger.error(f"精准提取失败: {e}")
            return f"[系统] 提取失败：{str(e)}"

    def _parse_round_numbers(self, expression: str) -> list:
        """
        解析轮次表达式为整数列表。
        
        Args:
            expression: 轮次表达式，如 '1,3-5,8'
        
        Returns:
            list: 去重且排序后的轮次列表
        """
        try:
            result_set = set()
            parts = expression.split(',')
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # 检测是否为范围表达式
                if '-' in part:
                    range_parts = part.split('-')
                    if len(range_parts) == 2:
                        try:
                            start = int(range_parts[0].strip())
                            end = int(range_parts[1].strip())
                            if start <= end:
                                result_set.update(range(start, end + 1))
                            else:
                                # 如果 start > end，交换
                                result_set.update(range(end, start + 1))
                        except ValueError:
                            continue
                else:
                    # 单个数字
                    try:
                        num = int(part)
                        result_set.add(num)
                    except ValueError:
                        continue
            
            # 返回升序列表
            return sorted(result_set)
            
        except Exception as e:
            logger.error(f"解析轮次表达式失败: {e}")
            return []

    def _build_temp_context(self, round_numbers: list) -> tuple:
        """
        从完整的历史记录中抽取目标轮次的消息。
        
        Args:
            round_numbers: 目标轮次列表，如 [1, 3, 5]
        
        Returns:
            tuple: (temp_messages, warnings)
                - temp_messages: 抽取出的消息列表
                - warnings: 警告信息（如超出范围的轮次）
        """
        temp_messages = []
        warnings = []
        
        # 计算总轮数
        total_rounds = len(self.client.chat_history) // 2
        
        for round_num in round_numbers:
            # 边界检查
            if round_num > total_rounds:
                warnings.append(f"第 {round_num} 轮超出当前对话范围（共 {total_rounds} 轮），已忽略")
                continue
            
            # 索引映射：第 N 轮对应索引 (N-1)*2 和 (N-1)*2 + 1
            user_idx = (round_num - 1) * 2
            assistant_idx = user_idx + 1
            
            # 提取 user 消息
            if user_idx < len(self.client.chat_history):
                temp_messages.append(self.client.chat_history[user_idx])
            
            # 提取 assistant 消息
            if assistant_idx < len(self.client.chat_history):
                temp_messages.append(self.client.chat_history[assistant_idx])
        
        return temp_messages, '; '.join(warnings) if warnings else ''
