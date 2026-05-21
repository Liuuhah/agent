"""
配置加载与状态管理 Mixin

职责：
- 加载 .env 配置文件并解析 API 基础信息
- 提供 Token 估算、对话轮数计算等基础工具方法
- 注册并执行本地工具（文件操作、网络请求等）
- 初始化所有共享状态（chat_history, system_prompt 等）

依赖关系：
- 无（作为继承链的最底层基类）

架构说明：
本模块是 ChatCompressClient 模块化拆分的基石。所有其他 Mixin 均直接或间接继承自此类。
"""
import os
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from ..tools import tools


class ConfigManagerMixin:
    """配置加载与状态管理 Mixin"""

    def __init__(self):
        self.config = self._load_config()
        self.base_url = self.config.get('BASE_URL')
        self.model = self.config.get('MODEL')
        self.token = self.config.get('TOKEN')
        self._parse_base_url()
        self.chat_history = []
        self.tools = self._register_tools()
        
        # 压缩配置
        self.max_rounds = 5
        self.max_context_tokens = 262144
        self.compress_ratio = 0.7
        
        # 压缩控制标志
        self.skip_next_compress = False
        self.auto_compress_enabled = True
        
        # 关键信息提取配置
        self.auto_extract_enabled = True
        self.skip_next_extract = False
        self.extract_interval = 5
        self.log_file_path = r"D:\chat-log\log.txt"
        
        # 累积式提取相关状态
        self.extract_message_counter = 0
        
        # 日志模式配置
        self.debug_mode = False
        
        # System Prompt 配置
        self.base_system_prompt = """你是一位经验丰富的宠物兽医助手，具有以下专业能力：
1. 宠物健康诊断：根据症状提供初步诊断建议
2. 喂养计划制定：根据年龄、体重、品种制定个性化喂养方案
3. 健康管理咨询：提供预防保健、疫苗接种等建议

【重要原则】
- 如果用户提到宠物的基本信息，请基于这些信息给出专业建议
- 始终保持温和专业的语气，避免引起宠物主人恐慌
- 对于紧急情况，务必建议立即就医
- 你不是真正的医生，仅提供参考建议，不能替代专业兽医诊断"""
        
        # 【流式中断】中断标志位
        self.is_interrupted = False
        self.system_prompt = self.base_system_prompt

    def _register_tools(self):
        """注册可用工具"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出指定目录下的所有文件和子目录",
                    "parameters": {
                        "type": "object",
                        "properties": {"directory_path": {"type": "string"}},
                        "required": ["directory_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rename_file",
                    "description": "修改某个目录下某个文件的名字",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string"},
                            "old_filename": {"type": "string"},
                            "new_filename": {"type": "string"}
                        },
                        "required": ["directory_path", "old_filename", "new_filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "删除某个目录下某个文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string"},
                            "filename": {"type": "string"}
                        },
                        "required": ["directory_path", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "在某个目录下新建一个文件并写入内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string"},
                            "filename": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["directory_path", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取某个目录下面的某个文件的内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string"},
                            "filename": {"type": "string"}
                        },
                        "required": ["directory_path", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "curl",
                    "description": "通过HTTP请求访问网页",
                    "parameters": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_chat_history",
                    "description": "搜索聊天历史记录",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "anythingllm_query",
                    "description": "查询本地文档仓库/知识库",
                    "parameters": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name, tool_args):
        """执行工具调用"""
        if tool_name == "list_directory":
            return tools.list_directory(tool_args.get("directory_path"))
        elif tool_name == "rename_file":
            return tools.rename_file(
                tool_args.get("directory_path"),
                tool_args.get("old_filename"),
                tool_args.get("new_filename")
            )
        elif tool_name == "delete_file":
            return tools.delete_file(
                tool_args.get("directory_path"),
                tool_args.get("filename")
            )
        elif tool_name == "create_file":
            return tools.create_file(
                tool_args.get("directory_path"),
                tool_args.get("filename"),
                tool_args.get("content", "")
            )
        elif tool_name == "read_file":
            return tools.read_file(
                tool_args.get("directory_path"),
                tool_args.get("filename")
            )
        elif tool_name == "curl":
            return tools.curl(tool_args.get("url"))
        elif tool_name == "search_chat_history":
            return tools.search_chat_history(tool_args.get("query"), debug=self.debug_mode)
        elif tool_name == "anythingllm_query":
            return tools.anythingllm_query(tool_args.get("message"), debug=self.debug_mode)
        return {"error": f"未知工具: {tool_name}"}

    def _load_config(self):
        """加载 .env 配置文件（使用项目根目录绝对路径）"""
        config = {}
        
        # Step 1: 计算项目根目录
        # _config_manager.py -> chat_compress_client/ -> ai_assistant/ -> src/ -> project_root/
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        
        # Step 2: 构建 .env 文件路径
        env_path = project_root / 'src' / '.env'
        
        # Step 3: 检查文件是否存在
        if not env_path.exists():
            print(f"❌ 错误: 未找到配置文件")
            print(f"   期望路径: {env_path}")
            print(f"   请确保在项目根目录下存在 src/.env 文件")
            exit(1)
        
        # Step 4: 读取并解析配置文件
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"').strip("'")
        except Exception as e:
            print(f"❌ 错误: 读取配置文件失败 - {e}")
            exit(1)
        
        return config

    def _parse_base_url(self):
        """解析 API 基础 URL"""
        parsed = urlparse(self.base_url)
        self.host = parsed.netloc
        self.path = parsed.path.rstrip('/')

    def _estimate_tokens(self, text):
        """粗略估算文本的 token 数量"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        return chinese_chars + (other_chars // 4)

    def _count_rounds(self):
        """计算对话轮数（一轮=user+assistant）"""
        return sum(1 for msg in self.chat_history if msg.get('role') == 'user')
