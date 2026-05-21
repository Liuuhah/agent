from ._logger import LoggerMixin


class ChatCompressClient(LoggerMixin):
    """AI 聊天压缩客户端主类（Facade）"""

    def set_system_prompt(self, additional_context: str):
        """动态更新 System Prompt，用于注入宠物档案"""
        self.system_prompt = self.base_system_prompt + "\n\n" + additional_context
        print(f"[系统] 已更新 System Prompt，注入宠物上下文信息")

    def reset_system_prompt(self):
        """重置 System Prompt 为基础版本"""
        self.system_prompt = self.base_system_prompt
        print(f"[系统] 已重置 System Prompt")

    def show_history_stats(self):
        """显示聊天历史统计信息"""
        rounds = self._count_rounds()
        context_tokens = sum(self._estimate_tokens(msg.get('content', '')) for msg in self.chat_history if 'content' in msg)
        message_count = len(self.chat_history)
        
        print(f"\n[聊天统计]")
        print(f"  消息数量: {message_count} 条")
        print(f"  对话轮数: {rounds} 轮")
        print(f"  上下文长度: {context_tokens} tokens")
        print(f"  压缩阈值: {self.max_rounds} 轮 或 {self.max_context_tokens} tokens")
        print()

    def run(self):
        """运行交互式聊天界面"""
        print("=" * 60)
        print("LLM 聊天压缩客户端（Practice03）")
        print("=" * 60)
        print(f"模型: {self.model}")
        print(f"API地址: {self.base_url}")
        print("=" * 60)
        print("核心功能:")
        print("  ✓ 自动检测对话轮数和上下文长度")
        print("  ✓ 超过5轮或3000 tokens时自动触发压缩")
        print("  ✓ 前70%内容LLM总结，后30%保留原文")
        print("  ✓ 支持工具调用（文件操作、网页访问）")
        print("=" * 60)
        print("可用命令:")
        print("  exit/quit - 退出程序")
        print("  clear     - 清空聊天历史")
        print("  debug     - 切换调试模式")
        print("  log       - 切换详细日志模式")
        print("  stats     - 显示聊天统计信息")
        print("  skip_compress / 跳过压缩 - 跳过下次自动压缩")
        print("  enable_compress / 启用压缩 - 启用自动压缩")
        print("  disable_compress / 禁用压缩 - 禁用自动压缩")
        print("  compress_settings / 压缩设置 - 显示压缩设置")
        print("  skip_extract / 跳过提取   - 跳过下次关键信息提取")
        print("  disable_extract / 禁用提取 - 禁用自动提取")
        print("  extract_settings / 提取设置 - 查看提取设置")
        print("  按 Ctrl+C 随时退出")
        print("=" * 60)
        print()
        
        debug_mode = False
        
        while True:
            try:
                user_input = input("你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    print("再见！")
                    break
                
                if user_input.lower() == 'clear':
                    self.clear_history()
                    continue
                
                if user_input.lower() == 'debug':
                    debug_mode = not debug_mode
                    status = "已启用" if debug_mode else "已禁用"
                    print(f"调试模式{status}")
                    continue
                
                if user_input.lower() == 'log':
                    self.debug_mode = not self.debug_mode
                    status = "已启用" if self.debug_mode else "已禁用"
                    print(f"📝 详细日志模式{status}")
                    continue
                
                if user_input.lower() == 'stats':
                    self.show_history_stats()
                    continue
                
                # 处理压缩控制命令
                if user_input.lower() in ['skip_compress', '跳过压缩']:
                    self.skip_next_compress = True
                    print("[设置] 下次将跳过自动压缩")
                    continue
                
                if user_input.lower() in ['enable_compress', '启用压缩']:
                    self.auto_compress_enabled = True
                    self.skip_next_compress = False
                    print("[设置] 已启用自动压缩")
                    continue
                
                if user_input.lower() in ['disable_compress', '禁用压缩']:
                    self.auto_compress_enabled = False
                    print("[设置] 已禁用自动压缩")
                    continue
                
                if user_input.lower() in ['compress_settings', '压缩设置']:
                    self._show_compress_settings()
                    continue
                
                # 处理关键信息提取控制命令
                if user_input.lower() in ['skip_extract', '跳过提取']:
                    self.skip_next_extract = True
                    print("[设置] 下次将跳过关键信息提取")
                    continue
                
                if user_input.lower() in ['enable_extract', '启用提取']:
                    self.auto_extract_enabled = True
                    self.skip_next_extract = False
                    print("[设置] 已启用自动提取")
                    continue
                
                if user_input.lower() in ['disable_extract', '禁用提取']:
                    self.auto_extract_enabled = False
                    print("[设置] 已禁用自动提取")
                    continue
                
                if user_input.lower() in ['extract_settings', '提取设置']:
                    self._show_extract_settings()
                    continue
                
                # ========== 处理 /search 命令 ==========
                if user_input.startswith('/search'):
                    query = user_input[7:].strip()
                    if not query:
                        query = "查找聊天历史"
                    
                    print(f"\n{'='*60}")
                    print(f"[搜索命令] 搜索关键词: {query}")
                    print(f"{'='*60}")
                    
                    from ..tools import tools
                    result = tools.search_chat_history(query, debug=self.debug_mode)
                    
                    if result.get('success'):
                        print(f"\n[搜索结果] {result.get('message')}")
                        if result.get('content'):
                            content = result.get('content')
                            clean_content = self._clean_extraction_content(content)
                            print(clean_content)
                        print(f"\n{'='*60}")
                    else:
                        print(f"\n[搜索失败] {result.get('message', result.get('error'))}")
                        print(f"\n{'='*60}")
                    continue
                
                # 累加 5W 提取计数器
                self.extract_message_counter += 1
                if self.debug_mode:
                    print(f"[调试] 5W 提取计数器: {self.extract_message_counter}")
                
                self.add_to_history('user', user_input)
                
                print("\nAI: ", end='', flush=True)
                response, time_taken = self.send_request_stream(user_input, debug=debug_mode)
                
                if response:
                    print()
                    self.add_to_history('assistant', response)
                    print(f"[耗时: {time_taken:.2f}秒]")
                    
                    # ========== AI 回复完成后，检查是否需要提取和压缩 ==========
                    if self.extract_message_counter > 0 and self.extract_message_counter % self.extract_interval == 0:
                        print("\n[系统触发] 检测到对话达到提取阈值，开始执行归档与清理...")
                        
                        if self.auto_extract_enabled and not self.skip_next_extract:
                            print("[系统触发] 步骤 1/2: 正在执行 5W 关键信息提取...")
                            self._extract_5w_info()
                        elif self.skip_next_extract:
                            self.skip_next_extract = False
                            print("[系统触发] 用户已跳过本次 5W 提取")
                        
                        if self._should_compress():
                            if self.auto_compress_enabled and not self.skip_next_compress:
                                print("\n[系统触发] 步骤 2/2: 正在执行上下文压缩...")
                                self._compress_chat_history()
                            elif self.skip_next_compress:
                                self.skip_next_compress = False
                                print("[系统触发] 用户已跳过本次上下文压缩")
                else:
                    print("\n抱歉，模型没有返回有效内容。")
                    self.chat_history.pop()
                
                print()
                
            except KeyboardInterrupt:
                print("\n\n收到中断信号，退出聊天...")
                break
            except Exception as e:
                print(f"\n发生错误: {e}")
                print("请重试或输入 'exit' 退出")
                print()

    def _clean_extraction_content(self, content):
        """清理提取内容，移除冗余思考过程（从 Tools 迁移过来以支持 /search）"""
        if not content: return content
        import re
        dialogue_match = re.search(r'\d+\.\s*\*{0,2}Analyze the Dialogue(?: Content)?\*{0,2}:', content)
        five_w_match = re.search(r'(?:^|\n)\s*-\s*(Who|What|When|Where|Why):', content, re.MULTILINE)
        if not five_w_match:
            five_w_match = re.search(r'(?:^|\n)(Who|What|When|Where|Why):', content, re.MULTILINE)
        
        if dialogue_match and five_w_match:
            return content[dialogue_match.start():].strip()
        elif five_w_match:
            return content[five_w_match.start():].strip()
        elif dialogue_match:
            return content[dialogue_match.start():].strip()
        
        thinking_markers = ['Thinking Process:', '思考过程', '分析过程', 'Let me think', 'First,', 'Second,', 'Finally,']
        for marker in thinking_markers:
            if marker in content:
                parts = content.split(marker, 1)
                if len(parts) > 1 and len(parts[1]) > 50:
                    return parts[1].strip()
        return content


if __name__ == "__main__":
    client = ChatCompressClient()
    client.run()
