import os
import sys
import json
import asyncio
import argparse
from typing import List, Dict, Any, Optional

import gradio as gr

# Import your existing client (must be alongside this file)
from mcp_client import LocalMCPClient


# ----------------------- Utilities -----------------------
def env_default(key: str, fallback: str) -> str:
    return os.getenv(key, fallback)


async def maybe_await(result):
    if asyncio.iscoroutine(result):
        return await result
    return result


def schema_to_text(schema: Any) -> str:
    try:
        return json.dumps(schema, ensure_ascii=False, indent=2) if schema else ""
    except Exception:
        return str(schema)


def tools_table_to_md(rows: List[List[str]]) -> str:
    """Render tool rows [[name, desc, schema_json], ...] into a Markdown table."""
    def esc(s: str) -> str:
        return (s or "").replace("|", "\\|").replace("\n", "<br>")
    md = ["| 名称 | 描述 | Schema |", "|---|---|---|"]
    for name, desc, schema in rows:
        md.append(f"| {esc(name)} | {esc(desc)} | <details><summary>展开</summary><pre>{esc(schema)}</pre></details> |")
    return "\n".join(md) if rows else "_未检测到工具。_"


# ----------------------- Core Ops -----------------------
async def connect_client(
    prompt_path: str,
    mcp_mode_by_url: str,
    vllm_url: str,
    model_name: str,
    api_key: str,
) -> Dict[str, Any]:
    # Sync env for downstream libs that read from environment
    if mcp_mode_by_url:
        os.environ["MCP_MODE_BY_URL"] = mcp_mode_by_url
    if vllm_url:
        os.environ["VLLM_API_URL"] = vllm_url
    if model_name:
        os.environ["MODEL_NAME"] = model_name
    if api_key is not None:
        os.environ["VLLM_API_KEY"] = api_key

    client = LocalMCPClient(prompt_path)

    # Some client methods may be sync/async depending on implementation
    if hasattr(client, "initialize_http_session"):
        await maybe_await(client.initialize_http_session())
    if hasattr(client, "connect_to_mcp"):
        await maybe_await(client.connect_to_mcp())

    # Prefer client.mcp_tools; otherwise try listing from session if present
    tools = []
    if getattr(client, "mcp_tools", None) is not None:
        tools = client.mcp_tools
    elif getattr(client, "mcp_session", None) is not None:
        try:
            resp = await client.mcp_session.list_tools()  # noqa
            tools = getattr(resp, "tools", [])
        except Exception:
            tools = []

    tools_table = []
    for t in tools or []:
        # Be defensive about attribute presence/types
        name = getattr(t, "name", "") if hasattr(t, "name") else t.get("name", "")
        desc = getattr(t, "description", "") if hasattr(t, "description") else t.get("description", "")
        schema = getattr(t, "schema", None) if hasattr(t, "schema") else t.get("schema", None)
        tools_table.append([name, desc, schema_to_text(schema)])

    status = (
        f"✅ 已连接：检测到 {len(tools_table)} 个工具。\n"
        f"- MCP_MODE_BY_URL = {os.getenv('MCP_MODE_BY_URL','')}\n"
        f"- VLLM_API_URL    = {os.getenv('VLLM_API_URL','')}\n"
        f"- MODEL_NAME      = {os.getenv('MODEL_NAME','')}"
    )
    return {"client": client, "status": status, "tools": tools_table}


async def send_message(
    message: str,
    history: List[List[str]],
    client: Optional[LocalMCPClient],
):
    if client is None:
        return history, "⚠️ 请先在上方完成连接。"

    try:
        reply = await maybe_await(client.process_query(message))
        history = (history or []) + [[message, reply or "（空响应）"]]
        return history, ""
    except Exception as e:
        history = (history or []) + [[message, f"出错了：{e}"]]
        return history, ""


async def clear_session(client: Optional[LocalMCPClient]):
    if client is not None and hasattr(client, "clear_chat_history"):
        try:
            await maybe_await(client.clear_chat_history())
            return [], "🧹 会话已清空。"
        except Exception as e:
            return [], f"清空失败：{e}"
    return [], "🧹 会话已清空。"


async def refresh_tools(client: Optional[LocalMCPClient]):
    if client is None:
        return [], "⚠️ 尚未连接。"

    try:
        tools_table = []
        # First try session list; else fallback to client's cached tools
        if getattr(client, "mcp_session", None) is not None:
            try:
                resp = await client.mcp_session.list_tools()
                tools = getattr(resp, "tools", [])
            except Exception:
                tools = getattr(client, "mcp_tools", []) or []
        else:
            tools = getattr(client, "mcp_tools", []) or []

        for t in tools:
            name = getattr(t, "name", "") if hasattr(t, "name") else t.get("name", "")
            desc = getattr(t, "description", "") if hasattr(t, "description") else t.get("description", "")
            schema = getattr(t, "schema", None) if hasattr(t, "schema") else t.get("schema", None)
            tools_table.append([name, desc, schema_to_text(schema)])

        # Keep cache aligned if attribute exists
        if hasattr(client, "mcp_tools"):
            client.mcp_tools = tools
        return tools_table, f"🔄 工具列表已刷新（{len(tools_table)} 个）。"
    except Exception as e:
        return [], f"刷新失败：{e}"


# ----------------------- Build UI (parametrized) -----------------------
def build_ui(initials: Dict[str, Any]):
    with gr.Blocks(title="MCP 可视化 Web 客户端", css="footer {visibility: hidden}") as demo:
        gr.Markdown("# 🧠 MCP 可视化 Web 客户端\n让本地 LLM + MCP 更直观地使用")

        with gr.Accordion("连接设置", open=True):
            with gr.Row():
                prompt_path = gr.Textbox(
                    label="Prompt 文件路径",
                    value=initials.get("prompt_path", "prompt.txt"),
                    placeholder="例如：prompt.txt",
                    scale=2
                )
                mcp_mode_by_url = gr.Textbox(
                    label="MCP 连接方式（stdio 路径 / SSE URL / sHTTP URL）",
                    value=initials.get("mcp_mode_by_url", env_default("MCP_MODE_BY_URL", "mcp_server.py")),
                    placeholder="mcp_server.py 或 http://host:port/sse / http://host:port/shttp",
                    scale=3
                )
            with gr.Row():
                vllm_url = gr.Textbox(
                    label="vLLM Chat Completions API",
                    value=initials.get("vllm_url", env_default("VLLM_API_URL", "http://192.168.50.208:8000/v1/chat/completions")),
                    scale=3
                )
                model_name = gr.Textbox(
                    label="模型名（model）",
                    value=initials.get("model_name", env_default("MODEL_NAME", "QwQ-32B-AWQ")),
                    scale=2
                )
                api_key = gr.Textbox(
                    label="API Key（如无需可留空）",
                    value=initials.get("api_key", env_default("VLLM_API_KEY", "")),
                    type="password",
                    scale=2
                )

            connect_btn = gr.Button("🔌 连接 / 启动")
            status_md = gr.Markdown("等待连接…")

        with gr.Accordion("🧰 已连接工具", open=True):
            tools_md = gr.Markdown("_尚未连接。_")
            refresh_btn = gr.Button("🔄 刷新工具列表")

        gr.Markdown("## 💬 对话")
        with gr.Row():
            chatbot = gr.Chatbot(label="对话")
        with gr.Row():
            user_msg = gr.Textbox(
                label="输入消息（回车发送）",
                placeholder="例如：设备indemind，先去卧室找一下垃圾桶，然后回到充电桩。",
            )
        with gr.Row():
            send_btn = gr.Button("发送")
            clear_btn = gr.Button("清空会话")

        # Gradio State for client instance
        client_state = gr.State(value=None)

        # Events
        async def on_connect(prompt_path, mcp_mode_by_url, vllm_url, model_name, api_key):
            bundle = await connect_client(
                prompt_path=prompt_path,
                mcp_mode_by_url=mcp_mode_by_url,
                vllm_url=vllm_url,
                model_name=model_name,
                api_key=api_key,
            )
            return (
                bundle["status"],                # status_md
                tools_table_to_md(bundle["tools"]),  # tools_md
                bundle["client"],                # client_state
            )

        connect_btn.click(
            on_connect,
            inputs=[prompt_path, mcp_mode_by_url, vllm_url, model_name, api_key],
            outputs=[status_md, tools_md, client_state],
            queue=True
        )

        async def on_send(message, history, client):
            updated_history, _ = await send_message(message, history or [], client)
            return updated_history, gr.update(value="")

        send_btn.click(
            on_send,
            inputs=[user_msg, chatbot, client_state],
            outputs=[chatbot, user_msg],
            queue=True
        )
        user_msg.submit(
            on_send,
            inputs=[user_msg, chatbot, client_state],
            outputs=[chatbot, user_msg],
            queue=True
        )

        async def on_clear(client):
            cleared, info = await clear_session(client)
            return cleared, gr.update(value=""), gr.update(value=info)

        clear_btn.click(
            on_clear,
            inputs=[client_state],
            outputs=[chatbot, user_msg, status_md],
            queue=True
        )

        async def on_refresh(client):
            data, info = await refresh_tools(client)
            return tools_table_to_md(data), gr.update(value=info)

        refresh_btn.click(
            on_refresh,
            inputs=[client_state],
            outputs=[tools_md, status_md],
            queue=True
        )

        # Auto-connect on load if requested via CLI
        if initials.get("auto_connect"):
            demo.load(
                on_connect,
                inputs=[prompt_path, mcp_mode_by_url, vllm_url, model_name, api_key],
                outputs=[status_md, tools_md, client_state],
                queue=True
            )

    return demo


# ----------------------- CLI -----------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="MCP 可视化 Web 客户端（Gradio）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("prompt_path", nargs="?", default="prompt.txt",
                   help="Prompt 文件路径（位置参数，可省略）")
    p.add_argument("--mcp", dest="mcp_mode_by_url", default=env_default("MCP_MODE_BY_URL", "mcp_server.py"),
                   help="MCP 连接方式：stdio 路径 / SSE URL / sHTTP URL")
    p.add_argument("--vllm", dest="vllm_url", default=env_default("VLLM_API_URL", "http://192.168.50.208:8000/v1/chat/completions"),
                   help="vLLM Chat Completions API 地址")
    p.add_argument("--model", dest="model_name", default=env_default("MODEL_NAME", "QwQ-32B-AWQ"),
                   help="模型名（model 字段）")
    p.add_argument("--api-key", dest="api_key", default=env_default("VLLM_API_KEY", "mindo"),
                   help="API Key（如无需可留空）")
    p.add_argument("--host", default="192.168.50.18", help="Gradio 监听地址（0.0.0.0 可供局域网访问）")
    p.add_argument("--port", type=int, default=7860, help="Gradio 端口")
    p.add_argument("--share", action="store_true", help="开启 Gradio share 外网隧道")
    p.add_argument("--auto-connect", action="store_true", help="页面加载后自动连接")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    initials = dict(
        prompt_path=args.prompt_path,
        mcp_mode_by_url=args.mcp_mode_by_url,
        vllm_url=args.vllm_url,
        model_name=args.model_name,
        api_key=args.api_key,
        auto_connect=args.auto_connect,
    )

    demo = build_ui(initials)
    demo.queue().launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        show_error=True,
    )


if __name__ == "__main__":
    main(sys.argv[1:])