## 环境依赖
`
pip install fastapi fastmcp
`

## 运行
### 改动
mcp_client.py 
- fine_path: prompt为本地prompt.txt地址
- line26-28: 目前api为indemind内部调用大模型接口，修改为本地可以调用的大模型接口

### 运行命令


`
export MCP_MODE_BY_URL=mcp_server.py
python mcp_client.py prompt_tools.txt
---
export MCP_MODE_BY_URL=http://192.168.50.22:8087/sse
python mcp_server.py
python mcp_client.py prompt_tools.txt
---
export MCP_MODE_BY_URL=http://192.168.50.22:8088/shttp
python mcp_server.py
python mcp_client.py prompt_tools.txt
`

### 输入示例
`
你: 设备123,左转1米后，前进1米
- batch_time_test
你:ttt

`
