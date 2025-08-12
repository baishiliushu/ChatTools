## 环境依赖
`
pip install fastapi fastmcp
`

## 运行
### 改动
llm_server_Qwen32B_mcp_example.py 
- fine_path: prompt为本地prompt.txt地址
- line26-28: 目前api为indemind内部调用大模型接口，修改为本地可以调用的大模型接口

### 运行命令


`
export MCP_MODE=stdio
export MCP_STDIO_SCRIPT=mcp_server.py
python llm_server_Qwen32B_mcp_example.py MCP_STDIO_SCRIPT prompt.txt
---
export MCP_MODE=sse
export MCP_SSE_URL=http://192.168.50.22:8087/sse
python mcp_server.py
python llm_server_Qwen32B_mcp_example.py MCP_SSE_URL prompt.txt
---
export MCP_MODE=shttp
export MCP_SHTTP_URL=http://192.168.50.22:8088/shttp
python mcp_server.py
python llm_server_Qwen32B_mcp_example.py MCP_SHTTP_URL prompt.txt
`

### 输入示例
`
你: 设备123,左转1米后，前进1米
你:ttt

`
