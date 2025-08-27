import asyncio
import os
import json
import sys
import time

import aiohttp
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client as shttp_client
from dotenv import load_dotenv
import logging
import httpx
from urllib.parse import urlparse
import datetime
import time

# Load .env
load_dotenv()

# 创建自定义格式化类
class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # 格式化时间为 "月-日 时:分:秒.毫秒"
        ct = self.converter(record.created)
        t = time.strftime("%m-%d %H:%M:%S", ct)
        s = "%s.%03d" % (t, record.msecs)
        return s

# 配置日志
def setup_logging():
    # 创建 logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 如果已有处理器存在，先清除
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 创建控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # 创建格式化器并使用自定义时间格式
    formatter = CustomFormatter('%(levelname)s %(asctime)s (%(message)s')
    
    # 将格式化器添加到处理器
    ch.setFormatter(formatter)
    
    # 将处理器添加到 logger
    logger.addHandler(ch)

# 设置日志
setup_logging()

# 获取 logger
logger = logging.getLogger("terminal_client")


class LocalMCPClient:
    def __init__(self, prompt_file_path = "prompt.txt"):
        self.exit_stack = AsyncExitStack()
        self.vllm_api_url = os.getenv("VLLM_API_URL", "http://192.168.50.208:8000/v1/chat/completions")
        self.model_name = os.getenv("MODEL_NAME", "QwQ-32B-AWQ")
        self.vllm_api_key = os.getenv("VLLM_API_KEY", "mindo")
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            self.file_content = f.read()

        self.mcp_session: Optional[ClientSession] = None
        self.mcp_tools: list = []
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.chat_history: List[Dict[str, Any]] = []
        self.test_queries = [
            "设备indemind, 现在几点了？",
            "设备indemind, 请你回到充电桩待命",
            "设备indemind, 往前走两米",
            "设备indemind, 请帮我找一下客厅的猫",
            "设备indemind, 去卧室靠近一下垃圾桶",
            "设备indemind, 请进行一次全屋的巡逻检查",
            "设备indemind, 先去书房找一下插排，然后回到充电桩",
            "设备indemind, 先去卧室找一下垃圾桶，找到后再去客厅找电视，然后回桩"
        ]
        self.mcp_mode = os.getenv("MCP_MODE_BY_URL", "mcp_server.py")  # stdio, sse, shttp

    async def initialize_http_session(self):
        if not self.http_session:
            # 配置连接池和超时参数
            connector = aiohttp.TCPConnector(
                limit=20,  # 最大连接数
                limit_per_host=5,  # 每主机最大连接数
                ttl_dns_cache=300  # DNS缓存时间
            )
            timeout = aiohttp.ClientTimeout(total=300)  # 总超时
            
            # 创建带配置的会话
            self.http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            
            try:
                # 注册到退出栈
                await self.exit_stack.enter_async_context(self.http_session)
            except Exception as e:
                # 如果注册失败，确保关闭会话
                await self.http_session.close()
                self.http_session = None
                raise e


    def convert_mcp_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        tools_openai_format = []
        for tool in self.mcp_tools:
            schema = tool.inputSchema if hasattr(tool, 'inputSchema') and isinstance(tool.inputSchema, dict) else {"type": "object", "properties": {}, "required": []}
            tools_openai_format.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": schema
                }
            })
        return tools_openai_format
    
    
    async def call_vllm_api(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, stream_enable: bool = False) -> Optional[Dict[str, Any]]:
        if not self.http_session:
            await self.initialize_http_session()
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            #"max_tokens": 90000,
            #"temperature": 0.5,
            "stream": stream_enable  # 启用流式输出
        }

        if tools:
            try:
                json.dumps(tools)  # Test serialization
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            except TypeError as e:
                logger.info(f"❌ 工具序列化失败: {e}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.vllm_api_key}"
        }

        logger.info(f"🔄 正在向 vLLM 发送请求 ({self.vllm_api_url})...{payload.keys()} \n{messages[0].keys()}")
        try:
            time_start_f = time.time()
            ret = {}
            async with self.http_session.post(self.vllm_api_url, headers=headers, json=payload, timeout=500) as response:
                if not stream_enable:
                    if response.status == 200:
                        logger.info(f"{type(response)}响应0: {response} ")

                        result = await response.json()
                        logger.info(f"🔍 原始 vLLM 响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}\n")
                        time_end_f = time.time()
                        logger.info("获取原始vLLM 响应 time cost: {:.2f} s".format(time_end_f - time_start_f))
                        if result.get("choices") or result is not None:
                            choice = result["choices"][0]
                            ret["tool_calls"] = choice["message"]["tool_calls"]
                            ret["content"] = choice["message"]["content"]
                                                   
                        return ret
                    else:
                        error_text = await response.text()
                        logger.info(f"❌ vLLM API 请求失败。状态码: {response.status}")
                        logger.info(f"响应内容: {error_text[:1000]}...")
                        return None
                else:
                    logger.info(f"{type(response)}响应1: {response} ")
                    
                    # 初始化变量用于累积流式数据
                    current_tool_calls = {}
                    ret_content = ""
                    
                    async for line in response.content:
                        if line:
                            decoded_line = line.decode('utf-8').strip()
                            logger.info(f"Received data: {decoded_line}")
                            
                            if decoded_line.startswith('data: '):
                                # 处理SSE格式数据
                                json_str = decoded_line[6:]  # 移除"data: "前缀
                                if json_str == "[DONE]":
                                    break
                                try:
                                    data = json.loads(json_str)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        
                                        # 处理内容更新
                                        if "content" in delta and delta["content"]:
                                            ret_content += delta["content"]
                                        
                                        # 处理工具调用更新
                                        if "tool_calls" in delta and delta["tool_calls"]:
                                            for tool_call_chunk in delta["tool_calls"]:
                                                index = tool_call_chunk.get("index", 0)
                                                
                                                # 初始化当前索引的工具调用
                                                if index not in current_tool_calls:
                                                    current_tool_calls[index] = {
                                                        "id": "",
                                                        "type": "function",
                                                        "function": {
                                                            "name": "",
                                                            "arguments": ""
                                                        }
                                                    }
                                                
                                                # 更新工具调用信息
                                                current_tool_call = current_tool_calls[index]
                                                
                                                if "id" in tool_call_chunk:
                                                    current_tool_call["id"] = tool_call_chunk["id"]
                                                
                                                if "type" in tool_call_chunk:
                                                    current_tool_call["type"] = tool_call_chunk["type"]
                                                
                                                if "function" in tool_call_chunk:
                                                    function_chunk = tool_call_chunk["function"]
                                                    
                                                    if "name" in function_chunk:
                                                        current_tool_call["function"]["name"] = function_chunk["name"]
                                                    
                                                    if "arguments" in function_chunk:
                                                        current_tool_call["function"]["arguments"] += function_chunk["arguments"]
                                    
                                    # 检查是否完成
                                    finish_reason = data["choices"][0].get("finish_reason")
                                    if finish_reason == "tool_calls":
                                        # 所有工具调用已完成，尝试解析参数
                                        ret_tool_calls = []
                                        for index in sorted(current_tool_calls.keys()):
                                            tool_call = current_tool_calls[index]
                                            try:
                                                # 尝试解析参数为JSON
                                                if tool_call["function"]["arguments"]:
                                                    tool_call["function"]["arguments"] = tool_call["function"]["arguments"]
                                                ret_tool_calls.append(tool_call)
                                            except json.JSONDecodeError:
                                                # 如果解析失败，保持原始字符串格式
                                                logger.warning(f"无法解析工具调用参数为JSON: {tool_call['function']['arguments']}")
                                                ret_tool_calls.append(tool_call)
                                        
                                        ret["tool_calls"] = ret_tool_calls
                                        ret["content"] = ret_content
                                        time_end_f = time.time()
                                        logger.info("获取原始vLLM 响应 time cost: {:.2f} s".format(time_end_f - time_start_f))
                                        return ret
                                        
                                except json.JSONDecodeError:
                                    logger.info(f"无法解析JSON: {json_str}")
                    
                    # 如果流结束但没有明确的工具调用完成信号，也尝试处理已收集的数据
                    ret_tool_calls = []
                    for index in sorted(current_tool_calls.keys()):
                        tool_call = current_tool_calls[index]
                        try:
                            if tool_call["function"]["arguments"]:
                                tool_call["function"]["arguments"] = tool_call["function"]["arguments"]
                            ret_tool_calls.append(tool_call)
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析工具调用参数为JSON: {tool_call['function']['arguments']}")
                            ret_tool_calls.append(tool_call)
                    
                    ret["tool_calls"] = ret_tool_calls
                    ret["content"] = ret_content
                    time_end_f = time.time()
                    logger.info("获取原始vLLM 响应 time cost: {:.2f} s".format(time_end_f - time_start_f))
                    return ret
                    

                    
                    # TODO: 解析到完整tool后判断
                    
                        # TODO: tool 不为空，放到ret中返回；tool为空，等待content拼接完后，放到ret中返回
                    

        except Exception as e:
            logger.info(f"❌ 调用 vLLM API 时发生意外错误: {e}")
            return None

    async def process_response(self, llm_response_data: Dict[str, Any], system_message: Dict[str, Any], query: str, stream_enable: bool = True) -> Optional[str]:
        """处理API响应（流式和非流式通用）"""
        if not llm_response_data or llm_response_data is None:
            return "抱歉，我在思考时遇到了一些麻烦。"

        content = llm_response_data.get("content")
        tool_calls = llm_response_data.get("tool_calls")
        
        llm_response_data["reasoning_content"] = None
        llm_response_data["role"] = "assistant"
        logger.info(f"响应后处理 -> 处理请求 {llm_response_data}")

        if tool_calls:
            tool_name_contents = []
            tool_name_description = ""
            tool_content_description = ""
            
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                try:
                    tool_args = json.loads(tool_call['function']['arguments'])
                except json.JSONDecodeError:
                    logger.info(f"❌ 工具参数解析失败: {tool_call['function']['arguments']}")
                    continue
                
                logger.info(f"🛠️ 真实 ToolCall: {tool_name}, 参数: {tool_args}")
                mcp_result = await self.mcp_session.call_tool(tool_name, tool_args)
                tool_content = mcp_result.content[0].text if mcp_result.content else "工具未返回任何内容。"
                tool_name_contents.append({"tool_name": tool_name, "tool_content": tool_content})
            
            for tc in tool_name_contents:
                tool_name_description += " " + tc["tool_name"] + "  "
                tool_content_description += " " + tc["tool_content"] + "  "
            
            twice_input = f"工具{tool_name_description}的请求结果:{tool_content_description}"
            if tool_content_description == "":
                ass = "请求工具结果出错。"
                self.chat_history.extend([{"role": "user", "content": query},{"role": "assistant", "content": ass}])
                return ass

            logger.info(f"🛠️ [-*-二次推理输入-*-] {twice_input}")
            tool_result_msg = {
                "role": "user",
                "content": twice_input
            }

            self.chat_history.extend([{"role": "user", "content": query}, llm_response_data, tool_result_msg])
            
            # 二次推理也使用相同的非流式模式设置                
            final_response = await self.call_vllm_api([system_message] + self.chat_history, stream_enable=False)
            if final_response and final_response.get("content"):
                final_content = final_response.get("content")
            else:
                final_response = "抱歉，处理工具结果时出错。"
            self.chat_history.append({"role": "assistant", "content": final_content})
            logger.info(f"\n🤖 Assistant: {final_content}")
            return final_content
        else:
            self.chat_history.extend([{"role": "user", "content": query}, llm_response_data])
            return content

    async def process_query(self, query: str, stream_enable: bool = False) -> Optional[str]:
        
        if not self.http_session:
            await self.initialize_http_session()
        querrys = query.split("c+++")
        if query.startswith("c+++") or len(self.chat_history) > 60:
            #self.chat_history = []
            await self.clear_chat_history()
        query = querrys[-1]
        if len(query) < 1:
            return "EMPTY user words."
        logger.info(f"发送请求到模型: {query}")
        system_message = {"role": "system", "content": self.file_content}
        messages = [system_message] + self.chat_history + [{"role": "user", "content": query}]
        tools_for_llm = self.convert_mcp_tools_to_openai_format()
        #print("openai mesages:\n{}".format(tools_for_llm))

        # 根据流式模式选择调用方式
        if stream_enable:
            logger.info("使用流式模式")
            #llm_response_data = await self.call_vllm_api_streaming(messages, tools=tools_for_llm)
        else:
            logger.info("使用非流式模式")
        llm_response_data = await self.call_vllm_api(messages, tools=tools_for_llm, stream_enable=stream_enable)
        return  await self.process_response(llm_response_data, system_message, query, stream_enable)      

    async def clear_chat_history(self):
        l = len(self.chat_history)
        self.chat_history = []
        print("\n已清空（{}条）会话历史".format(l))
        return len(self.chat_history)
        
    async def chat_loop(self):
        logger.info("\n🤖 本地 LLM + MCP 客户端已启动！输入 'quit' 退出")
        _stream_enable = False
        while True:
            try:
                query = input("\n你: ").strip()
                if not query:
                    continue
                if query.lower() == 'quit' or query.lower() == 'q':
                    break
                if query.lower() == 'ttt':
                    await self.run_batch_test()
                if query.lower() == 'stream on':
                    _stream_enable = True
                    logger.info("已启用流式模式")
                    continue
                if query.lower() == 'stream off':
                    _stream_enable = False
                    logger.info("已禁用流式模式")
                    continue
                if  query.lower() == 'c':
                    await self.clear_chat_history()
                else:
                    if _stream_enable:
                        print("🤖 Assistant: ", end="", flush=True)
                    response_text = await self.process_query(query, _stream_enable)
                    
            except KeyboardInterrupt:
                logger.info("\n检测到中断，正在退出...")
                break
            except Exception as e:
                logger.info(f"⚠️ 处理查询时发生错误: {str(e)}")          


    async def run_batch_test(self):
        system_message = {"role": "system", "content": self.file_content}
        tools_for_llm = self.convert_mcp_tools_to_openai_format()

        stats = []

        for i, query in enumerate(self.test_queries):
            messages = [system_message, {"role": "user", "content": query}]
            logger.info(f"\n🧪 测试 {i+1}/{len(self.test_queries)}: {query}")

            start = time.time()
            result = await self.call_vllm_api(messages, tools=tools_for_llm)
            end = time.time()

            duration = end - start
            stats.append((query, duration))
            logger.info(f"🕒 响应耗时: {duration:.2f} 秒\n")

        logger.info("\n📊 批量测试完成！\n")
        for query, duration in stats:
            logger.info(f"【{query}】耗时: {duration:.2f} 秒")

        all_times = [d for _, d in stats]
        logger.info(f"\n📈 平均耗时: {sum(all_times)/len(all_times):.2f} 秒")
        logger.info(f"⏱️ 最快: {min(all_times):.2f} 秒，最慢: {max(all_times):.2f} 秒")


    async def cleanup(self):
        logger.info("正在关闭连接...")
        await self.exit_stack.aclose()
        logger.info("连接已关闭。")

    
    async def _connect_stdio(self, server_script_path: str):
        """使用stdio模式连接"""
        if not os.path.isfile(server_script_path):
            raise FileNotFoundError(f"MCP Server 脚本未找到: {server_script_path}")

        command = "python" if server_script_path.endswith('.py') else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=os.environ.copy()
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            stdio_reader, stdio_writer = stdio_transport
            self.mcp_session = ClientSession(stdio_reader, stdio_writer)
            await self._initialize_session()
        except Exception as e:
            logger.info(f"❌ 使用 stdio 模式连接到 MCP Server 失败: {e}")
            raise

    async def _connect_sse(self, sse_url: str):
        """使用SSE模式连接 url默认 http://192.168.50.222:8087/sse"""
        try:
            os.environ.pop('ALL_PROXY', None)
            os.environ.pop('all_proxy', None)
                
            sse_transport = await self.exit_stack.enter_async_context(sse_client(sse_url))
            sse_reader, sse_writer = sse_transport
            self.mcp_session = ClientSession(sse_reader, sse_writer)
            await self._initialize_session()
        except Exception as e:
            logger.info(f"❌ 使用 SSE 模式连接到 MCP Server 失败: {e} BY {sse_url}")
            raise

    async def _connect_shttp(self, shttp_url: str):
        """使用sHTTP模式连接"""
        try:
            os.environ.pop('ALL_PROXY', None)
            os.environ.pop('all_proxy', None)
            shttp_transport = await self.exit_stack.enter_async_context(shttp_client(shttp_url))
            shttp_reader = None
            shttp_writer = None
            shttp_get_session_id = None
            if len(shttp_transport) > 1:
                shttp_reader, shttp_writer, shttp_get_session_id = shttp_transport
                #if rest:
                    #print(f"[DDDD] Additional elements: {rest}")
                    #shttp_get_session_id = rest[0]
                    #exit(8)
            else:
                exit(-3)
            self.mcp_session = ClientSession(shttp_reader, shttp_writer)
            await self._initialize_session()
        except Exception as e:
            logger.info(f"❌ 使用 sHTTP 模式连接到 MCP Server 失败: {e}")
            raise

    async def connect_to_mcp(self):
        """连接到MCP服务器，支持三种模式"""
        logger.info(f"尝试使用 {self.mcp_mode.upper()} 模式连接到 MCP 服务器...")
        mcp_mode_by_url = self.mcp_mode
        if ".py" in  mcp_mode_by_url:
            await self._connect_stdio(mcp_mode_by_url)
        elif "sse" in  mcp_mode_by_url:
            await self._connect_sse(mcp_mode_by_url)
        elif "shttp" in  mcp_mode_by_url:
            await self._connect_shttp(mcp_mode_by_url)
        else:
            raise ValueError(f"不支持的 MCP 模式: {self.mcp_mode}")

    async def _initialize_session(self):
        """初始化MCP会话"""
        await self.exit_stack.enter_async_context(self.mcp_session)
        await self.mcp_session.initialize()
        response = await self.mcp_session.list_tools()
        self.mcp_tools = response.tools
        
        if not self.mcp_tools:
            logger.info("⚠️ MCP Server 未报告任何可用工具。")
        else:
            logger.info("✅ 已连接到 MCP Server，支持以下工具:", [tool for tool in self.mcp_tools])


async def main():
    if len(sys.argv) < 2:
        logger.info("Usage: python client.py <path_to_prompt>")
        sys.exit(1)

    prompt_txt_path = sys.argv[1]
    client = LocalMCPClient(prompt_txt_path)
    try:
        await client.initialize_http_session()
      
        await client.connect_to_mcp()
        await client.chat_loop()

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

