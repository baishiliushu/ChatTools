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
python llm_server_Qwen32B_mcp_example.py server_whole.py prompt.txt
`

### 输入示例
`
你: 左转1米后，前进1米
`
