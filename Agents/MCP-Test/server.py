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
import logging

import asyncio
import datetime
import sys
import json


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
def get_robot_mcp_time():
    """Get current time.
    """
    now = datetime.datetime.now()
    # 格式化输出，例如  年-月-日 时:分:秒
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    formatted_time = "当前时间 {}".format(formatted_time)
    print("[Tool] {}".format(formatted_time))
    return {"type_task": "0", "status": formatted_time}


def indemind_check_areas(name):
    is_support = False
    AREAS = ["卧室", "客厅", "书房", "厨房", "餐厅", "卫生间", "阳台", "走廊", "unknown"]
    if name in AREAS:
        is_support = True
    return is_support


def indemind_check_items(name):
    is_support = False
    OBJECTS = ["鞋子", "垃圾桶", "底座", "线团", "插棑", "猫", "狗", "方桌", "圆桌", "体重称", "充电桩", "钥匙","椅子", "沙发", "床", "电视柜", "冰箱", "电视", "洗衣机", "电风扇", "遥控器", "鞋柜"]
    if name in OBJECTS:
        is_support = True
    return is_support


def indemind_task_id_map(task_id):
    descp = "暂不支持"
    tid = ""
    default_c = ""

    #TODO: convert based config-file
    #task_meanings = {"12": {"sdk_id":"12", "desp":"跟踪任务", "default_c":"好的，进入跟踪模式"}, "7":{"sdk_id":"7", "desp":"转动角度", "default_c":"开始转动"},}
    #if task_id in task_meanings.keys(): 
        #inner_dict = task_meanings[task_id]
        #tid = inner_dict['sdk_id']
        #descp = inner_dict['desp']
        #default_c = inner_dict['default_c']
    task_meanings = {"12": {"12":"跟踪任务-好的，进入跟踪模式"}, "7":{"7":"机器人转动任务-好的，转动"},}
    if task_id in task_meanings.keys():
        # list(task_meanings[task_id].keys())
        inner_dict = task_meanings[task_id]
        tid, descp_c = next(iter(inner_dict.items()))
        descp = descp_c.split("-")[0]
        default_c = descp_c.split("-")[:-1]
        
    return  tid, descp, default_c


def send_task(_cmd, _mac):
    """Send cmd to traget by WebSocket.
 
    :param _cmd: this is a first param
    :param _mac: this is a second param
    :returns: message sent sccessfully OR failed.
    :raises keyError: raises an exception
    """
    send_finished = 0
    # send cmd by websocket
    print("iBot {} -- DoW --> {}".format(_mac, _cmd))
    # recieve device-websocket
    return send_finished


def default_string_check(param, default_v):
    if param is None or param == "":
        param = default_v
    return param


def cmd_generate_by_keys(cont: str, expn: str, sid: str, tp: str, tc: str, tks: list) -> str:
    j_data = {
        "content": cont,
        "expression": expn,
        "session_id": sid,
        "type": tp
    }
    if tc is not None and tc != "":
        j_data["task_cont"] = tc
        j_data["tasks"] = tks
    j_string = json.dumps(j_data, ensure_ascii=False)
    return j_string


def indemind_err_enum(error_code):
    status_s = ["下发成功", "下发失败", "未知错误", "参数类型不合法", "待发布"]
    
    if error_code > len(status_s) or error_code < 0:
        error_code = 2    
    return status_s[error_code]


def task_sublist_generate(ttps):
    tasks = list()
    for index, tp in enumerate(ttps, start = 1):
        tp["task_id"]="{}".format(index)
        tasks.append(tp)
    return tasks
    

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
    
    cmd_stats =  4
    result = -1    
    return {"success": cmd_stats, "result": result}



def indemind_track_people(_id="127.0.0.1:8088", _content="", _session_id="", _expression=""):
    """Gen track-cmd and Send it.
    """
    socket_sent = 4
    task_mean = "跟踪任务"

    task_type_in_code = "12"
    #task_type, task_mean, default_c = indemind_task_id_map(task_type_in_code) 
    task_type = task_type_in_code
    defalut_c = "好的，进入跟踪模式"

    if task_type == "":
        return socket_sent, task_mean
    
    _content = default_string_check(_content, defalut_c)
    _expression = default_string_check(_expression, "喜悦")
    _session_id  = default_string_check(_expression, "967")
    _tasks = task_sublist_generate([{"task_type": "{}".format(task_type)}])
    cmd = cmd_generate_by_keys(_content, _expression, _session_id, "3", "1", _tasks)

    socket_sent = 1
    socket_sent = send_task(cmd, _id)
    return socket_sent, task_mean


@mcp.tool
def robot_track_people(device_id="127.0.0.1:8088", s_id="", context_llm="",  expression_llm=""):
    """[工具]启动机器人跟踪功能.
     
    参数
    ------------
    device_id : string
        被控设备的地址（？）
    s_id : string
        会话索引（？）
    context_llm : string
        播报的内容（可选）        
    expression_llm : string
        表情（可选） 
        
    返回值
    -------------
    dict
        机器人任务类型，下发状态
    """
    cmd_stats, type_task = indemind_track_people(_id=device_id, _content=context_llm, _session_id=s_id, _expression=expression_llm)
    status_description = indemind_err_enum(cmd_stats)
    print("[Tool] {} - {}".format(type_task, status_description))
    return {"type_task": type_task, "status": status_description}


def indemind_robot_rotation(rotation_angle=5.0, _id="127.0.0.1:8088", _content="", _session_id="", _expression=""):
    """Gen rotation-cmd and Send it.
    """
    socket_sent = 4
    task_mean = "机器人转动任务"

    task_type_in_code = "7"
    #task_type, task_mean, default_c = indemind_task_id_map(task_type_in_code) 
    task_type = task_type_in_code
    defalut_c = "即将转动 {} 度".format(rotation_angle)

    if task_type == "":
        return socket_sent, task_mean
    if not isinstance(rotation_angle, (int, float)):
        socket_sent = 3
        return socket_sent, task_mean
    
    _content = default_string_check(_content, defalut_c)
    _expression = default_string_check(_expression, "喜悦")
    _session_id  = default_string_check(_expression, "10")

        
    _tasks = task_sublist_generate([{"task_type": "{}".format(task_type), "rotation_angle": "{}".format(rotation_angle)}])
    cmd = cmd_generate_by_keys(_content, _expression, _session_id, "3", "1", _tasks)

    socket_sent = 1
    socket_sent = send_task(cmd, _id)
    return socket_sent, task_mean


@mcp.tool(description="控制机器人旋转")
def robot_rotation(device_id="127.0.0.1:8088", rotation_angle=5.0, s_id="", context_llm="",  expression_llm=""):
    """[工具]控制机器人旋转.
     
    参数
    ------------
    device_id : string
        被控机器人的设备号
    rotation_angle : float
        转动的角度值（左转为正，右转为负）    
        
    返回值
    -------------
    dict
        机器人任务类型，下发状态
    """
    cmd_stats, type_task = indemind_robot_rotation(rotation_angle=rotation_angle,_id=device_id, _content=context_llm, _session_id=s_id, _expression=expression_llm)
    status_description = indemind_err_enum(cmd_stats)
    print("[Tool] {} - {}".format(type_task, status_description))
    return {"type_task": type_task, "status": status_description}






if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="192.168.50.222", port=8008, path="/mcp")
