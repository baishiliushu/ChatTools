###################################
## env
# 1. pip install fastmcp
# 2. pip install fastapi
#
## run
# 0. IP http://0.0.0.0:8000/mcp 
# 1. python server.py
# 
#
## reference
# 1. [MCP] https://blog.csdn.net/z_344791576/article/details/148080576
########################################


from fastapi import FastAPI, Request, Response
from fastmcp import FastMCP
import datetime
import asyncio
import sys
import logging

# A FastAPI app
app = FastAPI()

@app.get("/items")
def list_items():
    return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"id": item_id, "name": f"Item {item_id}"}

@app.post("/items")
def create_item(name: str):
    return {"id": 3, "name": name}


# Create an MCP server from your FastAPI app
mcp = FastMCP.from_fastapi(app=app)

@mcp.tool()
def calculator(python_expression: str) -> dict:
    """For mathamatical calculation, always use this tool to calculate the result of a python expression. You can use 'math' or 'random' directly, without 'import'."""
    result = eval(python_expression, {"math": math, "random": random})
    #logger.info(f"Calculating formula: {python_expression}, result: {result}")
    return {"success": True, "result": result}

@mcp.tool
def get_current_time():
    """Get current time"""
    now = datetime.datetime.now()
    # 格式化输出，例如  年-月-日 时:分:秒
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


def indemind_task_id_map(task_id: str) -> str:
    task_meanings = {"12": "跟踪任务"}
    descp = "暂不支持"
    if task_id in task_meanings.keys():
        descp = task_meanings[task_id]
    return  descp
    
def indemind_track_people(_ip="127.0.0.1:8088", _content="", _session_id="", _expression=""):
    """"""
    task_type = "12"
    task_mean = indemind_task_id_map(task_type)
    cmd = """ {"content": "好的，进入跟踪模式","expression": "喜悦","session_id": "967","type": "3","task_cont": "1","tasks": [{"task_id": "1","task_type": "12"}]}"""
    # send cmd by websocket
    socket_sent = True
    print("{}".format(cmd))
    
    # recieve device-websocket
    socket_sent = True
        
    return socket_sent, task_mean
    

@mcp.tool
def robot_track_people(device_ip="127.0.0.1:8088", context_llm="", s_id="", expression_llm=""):
    """start track task"""
    cmd_stats, type_task = indemind_track_people(_ip=device_ip, _content=context_llm, _session_id=s_id, _expression=expression_llm)
    status_description = "未完成"
    if cmd_stats:
         status_description = "成功"
    return {"status": status_description, "type_task": type_task}


def indemind_search_person_reMsg():
    """"""
    cmd = """"""
    # send cmd by websocket
    socket_sent = True
    
    # recieve device-websocket
    running_result = 0
    return socket_sent, running_result


@mcp.tool 
def robot_gen_task_based_message_return(device_ip="", context_llm="", s_id="", expression_llm=""):
    """analysis reMesg"""
    
    cmd_stats =  False
    result = -1
    
    
    return {"success": cmd_stats, "result": result}




if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="192.168.50.222", port=8008, path="/mcp")
