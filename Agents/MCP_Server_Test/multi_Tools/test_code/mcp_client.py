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

# Load .env
load_dotenv()
logger = logging.getLogger("terminal_client")
logging.basicConfig(level=logging.DEBUG)

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
            self.http_session = aiohttp.ClientSession()
            await self.exit_stack.enter_async_context(self.http_session)

    async def connect_to_mcp_server(self, server_script_path: str):
        if not os.path.isfile(server_script_path):
            raise FileNotFoundError(f"MCP Server 脚本未找到: {server_script_path}")

        print(f"尝试连接到 MCP Server 脚本: {server_script_path}...")
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
            await self.exit_stack.enter_async_context(self.mcp_session)

            await self.mcp_session.initialize()
            response = await self.mcp_session.list_tools()
            self.mcp_tools = response.tools
            if not self.mcp_tools:
                print("⚠️ MCP Server 未报告任何可用工具。")
            else:
                print("✅ 已连接到 MCP Server，支持以下工具:", [tool.name for tool in self.mcp_tools])

        except Exception as e:
            print(f"❌ 连接到 MCP Server 失败: {e}")
            raise

    def convert_mcp_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        tools_openai_format = []
        for tool in self.mcp_tools:
            schema = tool.schema if hasattr(tool, 'schema') and isinstance(tool.schema, dict) else {"type": "object", "properties": {}, "required": []}
            tools_openai_format.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": schema
                }
            })
        return tools_openai_format

    async def call_vllm_api(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        if not self.http_session:
            await self.initialize_http_session()

        payload = {
            "model": self.model_name,
            "messages": messages,
            #"max_tokens": 90000,
            "temperature": 0.5,
        }

        if tools:
            try:
                json.dumps(tools)  # Test serialization
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            except TypeError as e:
                print(f"❌ 工具序列化失败: {e}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.vllm_api_key}"
        }

        print(f"🔄 正在向 vLLM 发送请求 ({self.vllm_api_url})...")
        try:
            time_start_f = time.time()
            async with self.http_session.post(self.vllm_api_url, headers=headers, json=payload, timeout=300) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"🔍 原始 vLLM 响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}\n")
                    time_end_f = time.time()
                    print("获取原始vLLM 响应 time cost: {:.2f} s".format(time_end_f - time_start_f))
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ vLLM API 请求失败。状态码: {response.status}")
                    print(f"响应内容: {error_text[:1000]}...")
                    return None

        except Exception as e:
            print(f"❌ 调用 vLLM API 时发生意外错误: {e}")
            return None

    async def process_query(self, query: str) -> Optional[str]:
        
        if not self.http_session:
            await self.initialize_http_session()
        querrys = query.split("c+++")
        if query.startswith("c+++") or len(self.chat_history) > 15:
            #self.chat_history = []
            await self.clear_chat_history()
        query = querrys[-1]
        if len(query) < 1:
            return "EMPTY user words."
        print(f"发送请求到模型: {query}")
        system_message = {"role": "system", "content": self.file_content}
        messages = [system_message] + self.chat_history + [{"role": "user", "content": query}]
        tools_for_llm = self.convert_mcp_tools_to_openai_format()
        #print("openai mesages:\n{}".format(tools_for_llm))
        llm_response_data = await self.call_vllm_api(messages, tools=tools_for_llm)

        if not llm_response_data:
            return "抱歉，我在思考时遇到了一些麻烦。"
        if llm_response_data.get("choices"):
                                                                                            
            choice = llm_response_data["choices"][0]
            message = choice["message"]
            #delta = choice.get('content', {})
            content = message.get("content")
            tool_calls = message.get("tool_calls")
            if tool_calls:
                toll_index = 0
                tool_name_contents = list()
                tool_name_description = ""
                tool_content_description = ""
                
                for toll_index in range(0, len(tool_calls)):
                    tool_call = tool_calls[toll_index]
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])

                    print(f"🛠️ 真实 ToolCall: {tool_name}, 参数: {tool_args}")
                    mcp_result = await self.mcp_session.call_tool(tool_name, tool_args)
                    tool_content = mcp_result.content[0].text if mcp_result.content else "工具未返回任何内容。"
                    tool_name_contents.append({"tool_name":tool_name, "tool_content":tool_content})
                
                for tc in tool_name_contents:
                    tool_name_description = tool_name_description + ";" + tc["tool_name"]
                    tool_content_description = tool_content_description + ";" + tc["tool_content"]

                tool_result_msg = {
                        "role": "user",
                        "content": f"工具 '{tool_name_description}' 执行完毕，返回：\n{tool_content_description}\n请回答用户的问题：'{query}'"
                    }    
                self.chat_history.extend([{"role": "user", "content": query}, message, tool_result_msg])

                final_response = await self.call_vllm_api([system_message] + self.chat_history)
                if final_response and final_response.get("choices"):
                    final_content = final_response["choices"][0]["message"].get("content")
                    self.chat_history.append({"role": "assistant", "content": final_content})
                    return final_content    
                else:
                    return "抱歉，处理工具结果时出错。" # 设备 b0:ac:82:47:d0:1d ,左转2度再转回来

            else:
                llm_content = message.get("content", "").strip()
                self.chat_history.extend([{"role": "user", "content": query}, message])
                return llm_content       
                                                           
    async def clear_chat_history(self):
        l = len(self.chat_history)
        self.chat_history = []
        print("\n已清空（{}条）会话历史".format(l))
        return len(self.chat_history)
        
    async def chat_loop(self):
        print("\n🤖 本地 LLM + MCP 客户端已启动！输入 'quit' 退出")
        while True:
            try:
                query = input("\n你: ").strip()
                if not query:
                    continue
                if query.lower() == 'quit' or query.lower() == 'q':
                    break
                if query.lower() == 'ttt':
                    await self.run_batch_test()
                if  query.lower() == 'c':
                    await self.clear_chat_history()
                else:
                    response_text = await self.process_query(query)
                    print(f"\n🤖 Assistant: {response_text}")
            except KeyboardInterrupt:
                print("\n检测到中断，正在退出...")
                break
            except Exception as e:
                print(f"⚠️ 处理查询时发生错误: {str(e)}")


    async def run_batch_test(self):
        system_message = {"role": "system", "content": self.file_content}
        tools_for_llm = self.convert_mcp_tools_to_openai_format()

        stats = []

        for i, query in enumerate(self.test_queries):
            messages = [system_message, {"role": "user", "content": query}]
            print(f"\n🧪 测试 {i+1}/{len(self.test_queries)}: {query}")

            start = time.time()
            result = await self.call_vllm_api(messages, tools=tools_for_llm)
            end = time.time()

            duration = end - start
            stats.append((query, duration))
            print(f"🕒 响应耗时: {duration:.2f} 秒\n")

        print("\n📊 批量测试完成！\n")
        for query, duration in stats:
            print(f"【{query}】耗时: {duration:.2f} 秒")

        all_times = [d for _, d in stats]
        print(f"\n📈 平均耗时: {sum(all_times)/len(all_times):.2f} 秒")
        print(f"⏱️ 最快: {min(all_times):.2f} 秒，最慢: {max(all_times):.2f} 秒")


    async def cleanup(self):
        print("正在关闭连接...")
        await self.exit_stack.aclose()
        print("连接已关闭。")

    
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
            print(f"❌ 使用 stdio 模式连接到 MCP Server 失败: {e}")
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
            print(f"❌ 使用 SSE 模式连接到 MCP Server 失败: {e} BY {sse_url}")
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
            print(f"❌ 使用 sHTTP 模式连接到 MCP Server 失败: {e}")
            raise

    async def connect_to_mcp(self):
        """连接到MCP服务器，支持三种模式"""
        print(f"尝试使用 {self.mcp_mode.upper()} 模式连接到 MCP 服务器...")
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
            print("⚠️ MCP Server 未报告任何可用工具。")
        else:
            print("✅ 已连接到 MCP Server，支持以下工具:", [tool.name for tool in self.mcp_tools])


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_prompt>")
        sys.exit(1)

    prompt_txt_path = sys.argv[1]
    client = LocalMCPClient(prompt_txt_path)
    try:
        await client.initialize_http_session()
        #await client.connect_to_mcp_server(mcp_server_script)
      
        await client.connect_to_mcp()
        await client.chat_loop()

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

