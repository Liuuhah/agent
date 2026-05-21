import os
import json
from datetime import datetime
import stat
import urllib.request
import urllib.error
import re
import subprocess
import time
from urllib.parse import quote, urlparse, urlunparse

class Tools:
    def list_directory(self, directory_path):
        """列出指定目录下的所有文件和子目录，包括文件的基本属性（大小、修改时间等）"""
        try:
            # 如果directory_path为None，返回错误
            if directory_path is None:
                return {"error": "未提供目录路径参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            if not os.path.exists(directory_path):
                return {"error": f"目录不存在: {directory_path}"}
            
            if not os.path.isdir(directory_path):
                return {"error": f"路径不是目录: {directory_path}"}
            
            items = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                item_stat = os.stat(item_path)
                
                item_info = {
                    "name": item,
                    "path": item_path,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": item_stat.st_size,
                    "last_modified": datetime.fromtimestamp(item_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "mode": stat.filemode(item_stat.st_mode)
                }
                items.append(item_info)
            
            return {"items": items, "total": len(items)}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def rename_file(self, directory_path, old_filename, new_filename):
        """修改某个目录下某个文件的名字"""
        try:
            # 检查参数
            if not directory_path or not old_filename or not new_filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 构建完整路径
            old_path = os.path.join(directory_path, old_filename)
            new_path = os.path.join(directory_path, new_filename)
            
            # 检查文件是否存在
            if not os.path.exists(old_path):
                return {"error": f"文件不存在: {old_path}"}
            
            # 检查新文件名是否已存在
            if os.path.exists(new_path):
                return {"error": f"新文件名已存在: {new_path}"}
            
            # 执行重命名
            os.rename(old_path, new_path)
            
            return {"success": True, "message": f"文件已重命名为: {new_filename}", "old_path": old_path, "new_path": new_path}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def delete_file(self, directory_path, filename):
        """删除某个目录下某个文件"""
        try:
            # 检查参数
            if not directory_path or not filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 构建完整路径
            file_path = os.path.join(directory_path, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            # 检查是否为文件
            if not os.path.isfile(file_path):
                return {"error": f"路径不是文件: {file_path}"}
            
            # 执行删除
            os.remove(file_path)
            
            return {"success": True, "message": f"文件已删除: {filename}", "deleted_path": file_path}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def create_file(self, directory_path, filename, content):
        """在某个目录下新建一个文件，并且写入内容"""
        try:
            # 检查参数
            if not directory_path or not filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 检查目录是否存在
            if not os.path.exists(directory_path):
                return {"error": f"目录不存在: {directory_path}"}
            
            if not os.path.isdir(directory_path):
                return {"error": f"路径不是目录: {directory_path}"}
            
            # 构建完整路径
            file_path = os.path.join(directory_path, filename)
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                return {"error": f"文件已存在: {file_path}"}
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content if content else '')
            
            return {"success": True, "message": f"文件已创建: {filename}", "file_path": file_path}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def read_file(self, directory_path, filename):
        """读取某个目录下面的某个文件的内容"""
        try:
            # 检查参数
            if not directory_path or not filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 构建完整路径
            file_path = os.path.join(directory_path, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            # 检查是否为文件
            if not os.path.isfile(file_path):
                return {"error": f"路径不是文件: {file_path}"}
            
            # 读取文件内容
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {"error": f"无法读取文件: {file_path}"}
            
            # 获取文件信息
            file_stat = os.stat(file_path)
            file_info = {
                "name": filename,
                "path": file_path,
                "size": file_stat.st_size,
                "last_modified": datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "mode": stat.filemode(file_stat.st_mode)
            }
            
            return {"success": True, "content": content, "file_info": file_info}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def curl(self, url):
        """通过curl访问网页，并返回网页内容"""
        try:
            # 检查参数
            if not url:
                return {"error": "缺少URL参数"}
            
            original_url = url
            
            # wttr.in 天气预报网站：允许 format 参数，支持 j1 格式获取结构化数据
            if 'wttr.in' in url:
                # 只清理 URL 格式问题，保留 format 参数
                url = re.sub(r'\?&', '?', url)
                url = re.sub(r'\?$', '', url)
                url = re.sub(r'&$', '', url)
            
            # 对 URL 进行编码，处理中文字符（如"成都" → "%E6%88%90%E9%83%BD"）
            parsed = urlparse(url)
            # 只对 path 部分进行编码，保留 query 参数
            encoded_path = quote(parsed.path, safe='/')
            encoded_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                encoded_path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            url = encoded_url
            
            # 执行HTTP请求
            # 对于 wttr.in，需要设置 User-Agent 为 "curl" 以获取文本格式而非 HTML
            if 'wttr.in' in url:
                req = urllib.request.Request(url, headers={'User-Agent': 'curl'})
                with urllib.request.urlopen(req) as response:
                    # 获取响应状态码
                    status_code = response.getcode()
                    # 获取响应头
                    headers = dict(response.getheaders())
                    # 获取内容类型
                    content_type = headers.get('Content-Type', '')
                    # 读取响应内容
                    content = response.read().decode('utf-8', errors='ignore')
            else:
                with urllib.request.urlopen(url) as response:
                    # 获取响应状态码
                    status_code = response.getcode()
                    # 获取响应头
                    headers = dict(response.getheaders())
                    # 获取内容类型
                    content_type = headers.get('Content-Type', '')
                    # 读取响应内容
                    content = response.read().decode('utf-8', errors='ignore')
                        
            # wttr.in 特殊处理：如果使用 format=j1，解析 JSON 并返回格式化文本
            if 'wttr.in' in original_url and 'format=j1' in original_url:
                try:
                    import json as json_module
                    weather_data = json_module.loads(content)
                    
                    # 检查是否是天气预报数据
                    if 'weather' in weather_data and len(weather_data['weather']) > 0:
                        # 默认查询明天（索引1），如果是今天则用索引0
                        day_index = 1 if len(weather_data['weather']) > 1 else 0
                        tomorrow = weather_data['weather'][day_index]
                        date_str = tomorrow.get('date', '未知日期')
                        
                        # 提取四个时段的数据（wttr.in 每小时一个数据点，共8个）
                        hourly_data = tomorrow.get('hourly', [])
                        if len(hourly_data) >= 8:
                            morning = hourly_data[2]   # 早晨
                            noon = hourly_data[4]      # 中午
                            evening = hourly_data[6]   # 傍晚
                            night = hourly_data[7]     # 夜间
                            
                            def format_period(period_data, period_name):
                                temp = period_data.get('tempC', 'N/A')
                                weather_desc = period_data.get('weatherDesc', [{}])[0].get('value', '未知')
                                wind_speed = period_data.get('windspeedKmph', 'N/A')
                                humidity = period_data.get('humidity', 'N/A')
                                precip_chance = period_data.get('chanceofrain', '0')
                                
                                return f"{period_name}\n" \
                                       f"   天气: {weather_desc}\n" \
                                       f"   温度: {temp}°C | 风力: {wind_speed} km/h | 湿度: {humidity}%\n" \
                                       f"   降水概率: {precip_chance}%"
                            
                            # 计算整体温度范围
                            all_temps = [int(h.get('tempC', 0)) for h in hourly_data if h.get('tempC')]
                            max_temp = max(all_temps) if all_temps else 'N/A'
                            min_temp = min(all_temps) if all_temps else 'N/A'
                            avg_temp = sum(all_temps) // len(all_temps) if all_temps else 'N/A'
                            
                            # 生成穿搭建议
                            dressing_advice = ""
                            if isinstance(avg_temp, int):
                                if avg_temp < 10:
                                    dressing_advice = "🧥 温度较低，建议穿厚外套、毛衣，注意保暖"
                                elif avg_temp < 20:
                                    dressing_advice = "👔 温度舒适偏凉，建议穿长袖T恤或薄外套"
                                elif avg_temp < 28:
                                    dressing_advice = "👕 温度温暖，建议穿短袖或轻薄衣物"
                                else:
                                    dressing_advice = "🩳 温度较高，建议穿透气轻薄的夏装，注意防晒"
                            
                            # 生成出行建议
                            travel_tips = []
                            morning_precip = int(morning.get('chanceofrain', 0))
                            if morning_precip > 50:
                                travel_tips.append("☔️ 早晨可能有雨，建议携带雨伞")
                            elif morning_precip > 20:
                                travel_tips.append("⛅ 早晨可能有零星小雨，可备折叠伞")
                            else:
                                travel_tips.append("✅ 早晨天气良好")
                            
                            evening_wind = int(evening.get('windspeedKmph', 0))
                            if evening_wind > 20:
                                travel_tips.append("💨 傍晚风力较大，注意防风")
                            elif evening_wind > 10:
                                travel_tips.append("💨 傍晚有微风，体感凉爽")
                            else:
                                travel_tips.append("💨 风力较小，体感舒适")
                            
                            # 生成格式化输出
                            formatted_weather = f"📅 天气预报 ({date_str})\n"
                            formatted_weather += f"{'='*60}\n\n"
                            formatted_weather += f"🌡️  整体概况：\n"
                            formatted_weather += f"   平均温度: {avg_temp}°C | 最高: {max_temp}°C | 最低: {min_temp}°C\n\n"
                            formatted_weather += f"{'='*60}\n\n"
                            formatted_weather += f"🕐 分时段详情：\n\n"
                            formatted_weather += format_period(morning, '🌅 早晨') + "\n\n"
                            formatted_weather += format_period(noon, '🌤️ 中午') + "\n\n"
                            formatted_weather += format_period(evening, '🌆 傍晚') + "\n\n"
                            formatted_weather += format_period(night, '🌃 夜间') + "\n\n"
                            formatted_weather += f"{'='*60}\n\n"
                            formatted_weather += f"💡 出行建议：\n"
                            for tip in travel_tips:
                                formatted_weather += f"   {tip}\n"
                            formatted_weather += f"   {dressing_advice}\n\n"
                            formatted_weather += f"{'='*60}"
                            
                            # 返回格式化后的内容，而不是原始 JSON
                            content = formatted_weather
                            content_type = 'text/plain; charset=utf-8'
                except Exception as e:
                    # 如果解析失败，返回原始内容
                    pass
            
            # wttr.in 经过格式化后已经是精简文本，不需要截断
            if 'wttr.in' in original_url:
                # 无论是文本格式还是格式化后的JSON，都保持完整
                pass
            elif 'json' in content_type:
                # 其他 JSON 格式保留更多
                content = content[:5000]
            elif 'html' in content_type:
                # HTML格式只保留前2000字符
                content = content[:2000] + '\n...[HTML内容已截断]...'
            else:
                # 其他格式保疙3000字符
                content = content[:3000]
                        
            return {
                "success": True,
                "url": url,
                "status_code": status_code,
                "content_type": content_type,
                "content": content
            }
        except urllib.error.URLError as e:
            return {"error": f"URL错误: {str(e)}"}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP错误: {e.code} - {e.reason}"}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def _clean_extraction_content(self, content):
        """清理提取内容，移除冗余思考过程，保留对话上下文和5W结果"""
        if not content:
            return content
        
        # 查找 "Analyze the Dialogue Content" 或 "Analyze the Dialogue" 的位置
        # 支持格式：2. **Analyze the Dialogue:** 或 2. **Analyze the Dialogue Content:**
        dialogue_match = re.search(r'\d+\.\s*\*{0,2}Analyze the Dialogue(?: Content)?\*{0,2}:', content)
        
        # 查找标准格式的 5W 结果（在行首，带 - 前缀或不带）
        # 排除 **Who:** 这种 Markdown 格式
        five_w_match = re.search(r'(?:^|\n)\s*-\s*(Who|What|When|Where|Why):', content, re.MULTILINE)
        
        # 如果没有找到带 - 的格式，尝试找不带 - 的格式（但要确保是在行首）
        if not five_w_match:
            five_w_match = re.search(r'(?:^|\n)(Who|What|When|Where|Why):', content, re.MULTILINE)
        
        if dialogue_match and five_w_match:
            # 两者都存在，保留从对话分析开始到结尾的所有内容
            start_pos = dialogue_match.start()
            clean_content = content[start_pos:].strip()
            return clean_content
        elif five_w_match:
            # 只有5W结果，保留5W部分
            start_pos = five_w_match.start()
            clean_content = content[start_pos:].strip()
            return clean_content
        elif dialogue_match:
            # 只有对话分析，保留对话分析部分
            start_pos = dialogue_match.start()
            clean_content = content[start_pos:].strip()
            return clean_content
        
        # 如果都没有匹配，尝试移除常见的思考过程标记
        thinking_markers = [
            'Thinking Process:',
            '思考过程',
            '分析过程',
            'Let me think',
            'First,',
            'Second,',
            'Finally,'
        ]
        
        for marker in thinking_markers:
            if marker in content:
                parts = content.split(marker, 1)
                if len(parts) > 1:
                    remaining = parts[1].strip()
                    # 检查剩余内容是否包含有用信息
                    if remaining and len(remaining) > 50:
                        return remaining.strip()
        
        # 如果都没有匹配，返回原始内容
        return content
    
    def _load_anythingllm_config(self):
        """加载 AnythingLLM 配置"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        config = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"')
                        except ValueError:
                            continue
        return config

    def anythingllm_query(self, message: str, debug: bool = False) -> dict:
        """
        使用 subprocess 调用 curl 命令，访问 AnythingLLM 知识库
        
        Args:
            message: 用户查询的问题
            debug: 是否输出调试信息
        
        Returns:
            {
                "success": True/False,
                "answer": "AI回答内容",
                "sources": [...],  # 引用来源（可选）
                "error": "错误信息"  # 仅在失败时存在
            }
        """
        if not message or not message.strip():
            return {"success": False, "error": "查询消息不能为空"}

        config = self._load_anythingllm_config()
        api_key = config.get('ANYTHINGLLM_API_KEY')
        workspace_slug = config.get('WORKSPACE_SLUG', 'ai')

        if not api_key:
            return {"success": False, "error": "缺少 ANYTHINGLLM_API_KEY 配置"}

        # 使用 127.0.0.1 而不是 localhost，避免 VPN 劫持
        url = f"http://127.0.0.1:3001/api/v1/workspace/{workspace_slug}/chat"
        
        if debug:
            print(f"[调试] 使用的 workspace slug: '{workspace_slug}'")
        
        # 修改为 chat 模式，保留上下文
        payload = json.dumps({"message": message, "mode": "chat"})
        
        start_time = time.time()
        
        try:
            # 尝试使用 curl (subprocess)
            cmd = [
                "curl", "-X", "POST",
                url,
                "-H", f"Authorization: Bearer {api_key}",
                "-H", "Content-Type: application/json",
                "-d", payload,
                "--max-time", "60"
            ]
            
            if debug:
                print(f"[调试] 发送请求到: {url}")
                print(f"[调试] 请求内容: {payload}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=65
            )
            
            if result.returncode != 0:
                raise Exception(f"Curl 执行失败: {result.stderr}")
            
            if debug:
                print(f"[调试] API 原始响应: {result.stdout[:500]}")
                
            response_data = json.loads(result.stdout)
            
            # 打印完整的响应结构，查看实际返回了什么字段
            if debug:
                print(f"[调试] 响应字段: {list(response_data.keys())}")
                print(f"[调试] textResponse: {response_data.get('textResponse', '不存在')}")
                print(f"[调试] response: {response_data.get('response', '不存在')}")
                print(f"[调试] message: {response_data.get('message', '不存在')}")
                print(f"[调试] sources: {response_data.get('sources', '不存在')}")
            
        except FileNotFoundError:
            # Windows 下可能没有 curl，使用 fallback
            if debug:
                print("[警告] 未找到 curl 命令，切换到 urllib 备用方案")
            return self._anythingllm_query_fallback(url, api_key, payload, debug)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "请求超时 (60秒)"}
        except json.JSONDecodeError:
            return {"success": False, "error": "API 响应格式错误"}
        except Exception as e:
            if debug:
                print(f"[错误] 查询异常: {str(e)}")
            return {"success": False, "error": f"查询异常: {str(e)}"}
        
        elapsed = time.time() - start_time
        if debug:
            print(f"[性能] AnythingLLM 查询耗时: {elapsed:.2f}秒")
        
        # 尝试多个可能的字段名
        answer = (response_data.get('textResponse') or 
                 response_data.get('response') or 
                 response_data.get('message') or 
                 '')
        
        sources = response_data.get('sources', [])
        
        # 确保返回的 answer 不为 None
        if answer is None:
            answer = ""
        
        if not answer and debug:
            print(f"[警告] API 未返回回答内容，完整响应: {json.dumps(response_data, ensure_ascii=False)[:300]}")
            
        return {
            "success": True,
            "answer": answer,
            "sources": sources
        }

    def _anythingllm_query_fallback(self, url, api_key, payload, debug=False):
        """urllib 备用方案"""
        try:
            if debug:
                print("[调试] 使用 urllib 备用方案发送请求")
            req = urllib.request.Request(
                url,
                data=payload.encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return {
                    "success": True,
                    "answer": response_data.get('textResponse', ''),
                    "sources": response_data.get('sources', [])
                }
        except Exception as e:
            if debug:
                print(f"[错误] 备用方案也失败: {str(e)}")
            return {"success": False, "error": f"备用方案也失败: {str(e)}"}

    def search_chat_history(self, query, debug=False):
        """搜索聊天历史记录，查找与查询相关的历史对话信息"""
        try:
            # 检查参数
            if not query:
                return {"error": "缺少查询参数，请提供搜索关键词"}
            
            log_file_path = r"D:\chat-log\log.txt"
            
            if debug:
                print(f"[调试] 正在搜索聊天记录: {query}")
            
            # 检查日志文件是否存在
            if not os.path.exists(log_file_path):
                return {
                    "success": False,
                    "message": "聊天记录文件不存在",
                    "details": f"文件路径: {log_file_path}",
                    "suggestion": "聊天记录尚未生成。请先进行至少5轮对话，系统会自动提取关键信息并保存。"
                }
            
            # 读取日志文件内容
            try:
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    log_content = f.read()
            except UnicodeDecodeError:
                # 尝试其他编码
                with open(log_file_path, 'r', encoding='gbk') as f:
                    log_content = f.read()
            
            # 检查文件是否为空
            if not log_content.strip():
                return {
                    "success": False,
                    "message": "聊天记录为空",
                    "details": "日志文件存在但没有内容",
                    "suggestion": "请先进行至少5轮对话，系统会自动提取关键信息并保存。"
                }
            
            # 统计记录条数
            record_count = log_content.count('【记录时间】')
            
            # 按记录分割：以 【记录时间】 为标记分割
            records = []
            current_record = []
            
            for line in log_content.split('\n'):
                if '【记录时间】' in line:
                    # 新记录开始
                    if current_record:
                        records.append('\n'.join(current_record).strip())
                    current_record = []
                current_record.append(line)
            
            # 添加最后一条记录
            if current_record:
                records.append('\n'.join(current_record).strip())
            
            # 过滤空记录
            records = [r for r in records if r.strip() and '【记录时间】' in r]
            
            # 调试日志
            if debug:
                print(f"[调试] 分割后得到 {len(records)} 条记录")
                for idx, record in enumerate(records):
                    print(f"[调试] 记录{idx+1} 前100字符: {record[:100]}")
            
            # 清理每条记录的内容（移除 Thinking Process）
            cleaned_records = []
            for record in records:
                clean_record = self._clean_extraction_content(record)
                if clean_record:
                    cleaned_records.append(clean_record)
            records = cleaned_records
            
            # 检查是否包含序号关键词
            target_records = []
            target_message = ""
            
            if '第一条' in query or '第1条' in query or '最早' in query or '首次' in query:
                # 返回第一条记录
                if len(records) > 0:
                    target_records = records[:1]
                    target_message = f"找到 {record_count} 条历史记录，以下是第一条："
                else:
                    return {
                        "success": False,
                        "message": "没有找到任何历史记录",
                        "total_records": 0
                    }
            elif '第二条' in query or '第2条' in query:
                # 返回第二条记录
                if len(records) > 1:
                    target_records = records[1:2]
                    target_message = f"找到 {record_count} 条历史记录，以下是第二条："
                else:
                    return {
                        "success": False,
                        "message": f"记录不足2条，当前只有 {len(records)} 条记录",
                        "total_records": record_count
                    }
            elif '第三条' in query or '第3条' in query:
                # 返回第三条记录
                if len(records) > 2:
                    target_records = records[2:3]
                    target_message = f"找到 {record_count} 条历史记录，以下是第三条："
                else:
                    return {
                        "success": False,
                        "message": f"记录不足3条，当前只有 {len(records)} 条记录",
                        "total_records": record_count
                    }
            else:
                # 默认返回最近3条记录
                target_records = records[-3:] if len(records) > 3 else records
                target_message = f"找到 {record_count} 条历史记录，以下是最近的 {len(target_records)} 条："
            
            target_content = '\n'.join(target_records)
            
            return {
                "success": True,
                "message": target_message,
                "total_records": record_count,
                "returned_records": len(target_records),
                "content": target_content
            }
        
        except FileNotFoundError:
            return {
                "error": "聊天记录文件不存在",
                "details": f"文件路径: {log_file_path}",
                "suggestion": "请先进行至少5轮对话，系统会自动提取关键信息并保存。"
            }
        except Exception as e:
            return {"error": f"搜索执行错误: {str(e)}"}

# 工具实例
tools = Tools()
