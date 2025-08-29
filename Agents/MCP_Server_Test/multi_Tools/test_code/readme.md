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
python mcp_server.py 2>&1 | tee -a "../../../Logs/$(date +"%y_%m_%d-%H_%M_%S")-server.log"

python mcp_client.py prompt_tools.txt
---
export MCP_MODE_BY_URL=http://192.168.50.22:8088/shttp
python mcp_server.py
python mcp_client.py prompt_tools.txt 2>&1 | tee -a "../../../Logs/$(date +"%y_%m_%d-%H_%M_%S")-client.log"
`

### 输入示例
`
你: 设备123,左转1米后，前进1米
- batch_time_test
你:ttt

`  

### 统计命令  
`  
 #25_08_29-14_36_44-batch-32B.log Logs/25_08_29-14_17_04-batch-32B.log  1.72673
file_name="25_08_29-14_36_44-batch-32B.log"  

cat ${file_name} | grep "tool time " | wc -l

cat ${file_name} | grep "tool time" | awk -F'cost: ' '{print $2}' | awk -F' s' '{print $1}' | awk '{sum+=$1} END {print "", sum/NR}'

cat ${file_name} | grep "tool time" | awk -F'cost: ' '{print $2}' | awk -F' s' '{print $1}' | awk 'BEGIN {max = 0} {if ($1+0>max+0) max=$1 fi} END {print "Max=", max}'
cat ${file_name} | grep "tool time" | awk -F'cost: ' '{print $2}' | awk -F' s' '{print $1}' | awk 'BEGIN{min = 65536}{if ($1+0<min+0) min=$1 fi}END{print "Min=", min}'
cat ${file_name} | grep "tool time"| awk -F'cost: ' '{time = $2; sub(/ s.*/, "", time); if(time > 1.8) print $0}' | wc -l

`
