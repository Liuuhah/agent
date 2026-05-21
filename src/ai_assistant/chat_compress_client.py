"""
兼容层：从子包导入主类

注意：此文件仅用于保持向后兼容，新代码应直接使用：
    from ai_assistant.chat_compress_client.main import ChatCompressClient
或
    from ai_assistant.chat_compress_client import ChatCompressClient
"""

from .chat_compress_client.main import ChatCompressClient

__all__ = ['ChatCompressClient']
