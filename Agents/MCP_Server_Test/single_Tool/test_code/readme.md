## 环境依赖
`
pip install fastapi fastmcp
`

## 运行
### 改动

- fine_path: prompt为本地prompt.txt地址
- line26-28: 目前api为大模型接口

### 运行命令
`
1. stdio  
export MCP_MODE_BY_URL=mcp_server.py;
python mcp_client.py prompt_tools.txt
---
2. sse(IP using your own;endless of url must be "sse")  
export MCP_MODE_BY_URL=http://192.168.50.22:8087/sse;
python mcp_server.py
python mcp_client.py prompt_tools.txt
---
3. sHTTP(IP using your own;endless of url must be "shttp")  
export MCP_MODE_BY_URL=http://192.168.50.22:8088/shttp;
python mcp_server.py
python mcp_client.py prompt_tools.txt
`

### 输入示例
`
你: 左转1米后，前进1米
`
