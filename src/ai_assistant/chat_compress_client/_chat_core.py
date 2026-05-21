"""
基础聊天与流式输出 Mixin

职责：
- 处理与 LLM API (LM Studio) 的 HTTP 通信
- 实现流式响应接收与实时打印
- 管理工具调用的多轮循环逻辑
- 维护消息序列的合法性（避免 Jinja 模板错误）

依赖关系：
- ConfigManagerMixin: 获取 base_url, token, model 等配置

架构说明：
本模块负责核心的“对话”功能。它依赖于底层的配置，并为上层的压缩和提取提供数据基础。
"""
import json
import time
import sys
import threading
import http.client
import os
from ._config_manager import ConfigManagerMixin


class ChatCoreMixin(ConfigManagerMixin):
    """基础聊天与流式输出 Mixin"""

    def send_request_stream(self, prompt, max_tokens=4096, debug=None, temperature=0.6):
        """发送流式请求，实时输出回复内容（带自动压缩功能）"""
        if debug is None:
            debug = self.debug_mode
        
        start_time = time.time()
        full_content = ''
        max_tool_rounds = 3
        
        for round_num in range(max_tool_rounds):
            content, has_tool_call = self._send_single_stream(
                prompt, max_tokens, debug, round_num == 0, temperature
            )
            if content:
                full_content = content
            if not has_tool_call or round_num >= max_tool_rounds - 1:
                break
        
        end_time = time.time()
        return full_content, end_time - start_time

    def _clean_message_sequence(self, messages):
        """清理消息序列，避免连续相同角色的消息导致 Jinja 模板错误"""
        if not messages:
            return []
        
        cleaned = []
        for msg in messages:
            role = msg.get('role')
            if role == 'system' and not msg.get('content', '').strip():
                continue
            
            if cleaned and cleaned[-1].get('role') == role:
                if role in ['user', 'assistant', 'system']:
                    prev_content = cleaned[-1].get('content', '')
                    curr_content = msg.get('content', '')
                    if isinstance(curr_content, dict):
                        curr_content = json.dumps(curr_content)
                    cleaned[-1]['content'] = prev_content + '\n\n' + str(curr_content)
            else:
                cleaned.append(msg.copy())
        return cleaned

    def _send_single_stream(self, prompt, max_tokens, debug, is_first_round, temperature=0.6):
        """发送单次流式请求，返回(内容, 是否有工具调用)"""
        if debug:
            print(f"\n{'='*60}\n[调试] 开始发送流式请求\n{'='*60}\n")
        
        conn = http.client.HTTPSConnection(self.host) if self.base_url.startswith('https://') else http.client.HTTPConnection(self.host)
        
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        cleaned_history = self._clean_message_sequence(self.chat_history)
        messages_list = [{'role': 'system', 'content': self.system_prompt}]
        
        if cleaned_history and cleaned_history[-1].get('role') == 'user' and cleaned_history[-1].get('content') == prompt:
            messages_list.extend(cleaned_history)
        else:
            messages_list.extend(cleaned_history)
            messages_list.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': self.model,
            'messages': messages_list,
            'tools': self.tools,
            'tool_choice': 'auto',
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': True
        }
        
        try:
            conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
            response = conn.getresponse()
            if response.status != 200:
                return "", False
        except Exception as e:
            print(f"[错误] 发送请求时发生异常: {e}")
            return "", False
        
        full_content = ''
        buffer = ''
        self.is_interrupted = False
        label_printed = False
        
        # 【流式中断】启动后台键盘监听线程（仅 Windows）
        listener_thread = None
        if sys.platform == 'win32':
            listener_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
            listener_thread.start()
        
        tool_calls_buffer = {}
        pending_tool_calls = []
        tool_call_response = ''
        
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'chat_{time.strftime("%Y%m%d_%H%M%S")}.txt')
        
        try:
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                
                buffer += chunk.decode('utf-8', errors='ignore')
                lines = buffer.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('data: '):
                        json_str = line[6:].strip()
                        if json_str == '[DONE]':
                            if pending_tool_calls:
                                for tool_call_data in pending_tool_calls:
                                    response_content = self._execute_pending_tool_call(
                                        tool_call_data, data, conn, headers, prompt
                                    )
                                    if response_content:
                                        tool_call_response = response_content
                                return tool_call_response if tool_call_response else full_content, False
                            return full_content, False
                        
                        try:
                            chunk_data = json.loads(json_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                
                                if 'tool_calls' in delta:
                                    for tc in delta['tool_calls']:
                                        index = tc.get('index', 0)
                                        if index not in tool_calls_buffer:
                                            tool_calls_buffer[index] = {'id': None, 'type': 'function', 'function': {'name': None, 'arguments': ''}}
                                        
                                        if 'id' in tc: tool_calls_buffer[index]['id'] = tc['id']
                                        if 'function' in tc:
                                            if 'name' in tc['function']: tool_calls_buffer[index]['function']['name'] = tc['function']['name']
                                            if 'arguments' in tc['function']: 
                                                tool_calls_buffer[index]['function']['arguments'] += tc['function']['arguments']
                                        
                                        args_str = tool_calls_buffer[index]['function']['arguments']
                                        if args_str:
                                            try:
                                                tool_args = json.loads(args_str)
                                                tool_name = tool_calls_buffer[index]['function']['name']
                                                if tool_name:
                                                    pending_tool_calls.append({'id': tool_calls_buffer[index]['id'], 'name': tool_name, 'arguments': tool_args})
                                            except json.JSONDecodeError: pass
                                
                                content = delta.get('content', '')
                                if content:
                                    if self.is_interrupted:
                                        print("\n[已暂停输出]", end="", flush=True)
                                        if pending_tool_calls:
                                            for tool_call_data in pending_tool_calls:
                                                response_content = self._execute_pending_tool_call(tool_call_data, data, conn, headers, prompt)
                                                if response_content: tool_call_response = response_content
                                        return tool_call_response if tool_call_response else full_content, False
                                    
                                    # 【新增】首次输出时打印标签
                                    if not label_printed and is_first_round:
                                        print("\n[AI 管家]: ", end='', flush=True)
                                        label_printed = True
                                    
                                    print(content, end='', flush=True)
                                    full_content += content
                                    if debug:
                                        with open(log_file, 'a', encoding='utf-8') as f:
                                            f.write(content)
                        except json.JSONDecodeError: pass
                
                buffer = lines[-1] if lines else ''
        except KeyboardInterrupt:
            return full_content, False
        finally:
            conn.close()
            
            # 【新增】流式输出结束后换行
            if full_content:
                print()  # 换行，避免与后续日志混在一起
        
        if pending_tool_calls and not tool_call_response:
            for tool_call_data in pending_tool_calls:
                response_content = self._execute_pending_tool_call(tool_call_data, data, conn, headers, prompt)
                if response_content: tool_call_response = response_content
            return tool_call_response if tool_call_response else full_content, False
        
        return full_content, False

    def _execute_pending_tool_call(self, tool_call_data, data, conn, headers, prompt):
        """执行累积完整的工具调用"""
        tool_id = tool_call_data['id']
        tool_name = tool_call_data['name']
        tool_args = tool_call_data['arguments']
        
        print(f"\n完整工具调用: {tool_name}")
        normalized_tool_name = tool_name.lower()
        tool_result = self.execute_tool(normalized_tool_name, tool_args)
        print(f"工具执行结果: {json.dumps(tool_result, ensure_ascii=False)}")
        
        self.add_to_history('assistant', {
            'tool_calls': [{'id': tool_id, 'type': 'function', 'function': {'name': tool_name, 'arguments': json.dumps(tool_args, ensure_ascii=False)}}]
        })
        self.add_to_history('tool', {
            'tool_call_id': tool_id, 'name': tool_name, 'content': json.dumps(tool_result, ensure_ascii=False)
        })
        
        print("\nAI: ", end='', flush=True)
        conn.close()
        
        conn = http.client.HTTPSConnection(self.host) if self.base_url.startswith('https://') else http.client.HTTPConnection(self.host)
        cleaned_history = self._clean_message_sequence(self.chat_history)
        messages_list = [{'role': 'system', 'content': self.system_prompt}]
        
        if cleaned_history and cleaned_history[-1].get('role') == 'user' and cleaned_history[-1].get('content') == prompt:
            messages_list.extend(cleaned_history)
        else:
            messages_list.extend(cleaned_history)
            messages_list.append({'role': 'user', 'content': prompt})
        
        data['messages'] = messages_list
        data['tool_choice'] = 'none'
        
        conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
        response = conn.getresponse()
        
        full_content = ''
        buffer = ''
        try:
            while True:
                chunk = response.read(1024)
                if not chunk: break
                buffer += chunk.decode('utf-8', errors='ignore')
                lines = buffer.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('data: '):
                        json_str = line[6:].strip()
                        if json_str == '[DONE]': continue
                        try:
                            chunk_data = json.loads(json_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    full_content += content
                        except json.JSONDecodeError: pass
                buffer = lines[-1] if lines else ''
        finally:
            conn.close()
        return full_content

    def add_to_history(self, role, content):
        """添加消息到聊天历史（自动附加 round_id）"""
        current_round = (len([m for m in self.chat_history if m.get('role') == 'user']) + (1 if role == 'user' else 0))
        message = {'role': role, 'round_id': current_round}
        
        if role == 'assistant' and isinstance(content, dict) and 'tool_calls' in content:
            message.update(content)
        elif role == 'tool' and isinstance(content, dict):
            message.update(content)
        else:
            message['content'] = content
        self.chat_history.append(message)

    def clear_history(self):
        """清空聊天历史"""
        self.chat_history = []
        print("聊天历史已清空")
