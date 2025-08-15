from fastapi import FastAPI
from fastmcp import FastMCP
import logging
from datetime import datetime
from typing import List, Optional, Tuple
import random
import uuid
import json  # 新增：用于打印 task_json
import os

# ---------------------------- 初始化 ----------------------------
app = FastAPI()
mcp = FastMCP.from_fastapi(app=app)
logger = logging.getLogger("luna_mcp")
logging.basicConfig(level=logging.INFO) #level=logging.DEBUG

# ---------------------------- prompt.md 对齐的枚举 ----------------------------
AREAS = ["卧室", "客厅", "书房", "厨房", "餐厅", "卫生间", "阳台", "走廊", "unknown"]

OBJECTS = [
    "鞋子", "垃圾桶", "底座", "线团", "插棑", "猫", "狗",
    "方桌", "圆桌", "体重称", "充电桩", "钥匙", "行人", "椅子", "沙发",
    "床", "电视柜", "冰箱", "电视", "洗衣机", "电风扇", "遥控器", "鞋柜"
]

EXPRESSIONS = ["默认", "喜悦", "担忧", "好奇", "思考", "疲惫", "生气", "害怕"]

TT = {
    "PersonSearch": "1",
    "SemanticObjSearch": "2",
    "GoToChargingStation": "3",
    "MoveToSemanticObj": "4",
    "FindObjInSemanticObj": "5",
    "PointToPoint": "6",
    "Rotate": "7",
    "Move": "8",
    "ControlTV": "9",
    "CreateMap": "10",
    "RetrunZero": "11",
    "TrackPerson": "12",
    "SecurityInspection": "13",
    "Reserved_1": "14",
    "Dance": "15"
}

TC = {
    "Normal": "1",
    "Clear": "2",
    "Update": "3",
    "Continue": "4",
    "Pause": "5",
}

# ---------------------------- 公共方法 ----------------------------
def _session_id() -> str:
    return str(random.randint(0, 1000))

def _expression_or_default(expr: Optional[str]) -> str:
    return expr if expr in EXPRESSIONS else "默认"

def _build_broadcast(content: str, expression: Optional[str] = "默认", session_id: Optional[str] = None) -> dict:
    return {
        "content": content,
        "expression": _expression_or_default(expression),
        "session_id": session_id or _session_id(),
        "type": "2"
    }

def _build_task(content: str,
                expression: Optional[str],
                task_cont: str,
                tasks: List[dict],
                session_id: Optional[str] = None) -> dict:
    return {
        "content": content,
        "expression": _expression_or_default(expression),
        "session_id": session_id or _session_id(),
        "type": "3",
        "task_cont": task_cont,
        "tasks": tasks
    }

# ---------------------------- 返回结构工具函数 ----------------------------
def _build_response(device_id: str, task_type: str, status: str = "下发成功",
                    message: str = "", error_code: str | None = None) -> dict:
    detail = {
        "requestId": str(uuid.uuid4()),
        "message": message or ""
    }
    if error_code:
        detail["errorCode"] = error_code
    return {
            "deviceId": device_id,
            "result":
                {
                    "taskType": task_type,
                    "status": status
                }
        }

def _dedup_preserve(seq: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _ok(msg: str = "") -> Tuple[bool, str]:
    return True, msg

def _fail(msg: str) -> Tuple[bool, str]:
    return False, msg

def _require_device(deviceId: str) -> Tuple[bool, str]:
    if not isinstance(deviceId, str) or not deviceId.strip():
        return _fail("deviceId 不能为空。请传入有效的设备标识字符串。")
    return _ok()

def _require_expression(expr: Optional[str]) -> Tuple[bool, str]:
    if expr is None or expr == "":
        return _ok()
    if expr not in EXPRESSIONS:
        return _fail(f"不支持的表情：{expr}。可选：{', '.join(EXPRESSIONS)}")
    return _ok()

def _require_float(name: str, val) -> Tuple[bool, str, Optional[float]]:
    try:
        f = float(val)
        return True, "", f
    except Exception:
        return False, f"{name} 需要为数字，例如 0.5 或 -0.3。", None

def _require_nonzero(name: str, f: float) -> Tuple[bool, str]:
    if f == 0.0:
        return _fail(f"{name} 不能为 0。")
    return _ok()

# ✅ 固定返回三元组 (ok, msg, areas)
def _validate_areas(areas: Optional[List[str]], required: bool = False) -> Tuple[bool, str, Optional[List[str]]]:

    if areas is None:
        if required:
            return False, "areas 不能为空，请至少指定 1 个区域。", None
        return True, "", None
    if not isinstance(areas, list):
        return False, "areas 需要为字符串列表。", None
    areas = _dedup_preserve([str(a).strip() for a in areas if str(a).strip()])
    if len(areas) < 1:
        if not required:
            return True, "", areas
        else:
            return False, "areas 不能为空，请至少指定 1 个区域。", None

    invalid = [a for a in areas if a not in AREAS]
    if invalid:
        return False, f"不支持的区域：{', '.join(invalid)}。可选：{', '.join(AREAS)}", None
    return True, "", areas

# ✅ 固定返回三元组 (ok, msg, objs)
def _validate_objects(objs: Optional[List[str]], required: bool = True) -> Tuple[bool, str, Optional[List[str]]]:
    if objs is None:
        if required:
            return False, "object 不能为空，请至少指定 1 个语义物体。", None
        return True, "", None
    if not isinstance(objs, list):
        return False, "object 需要为字符串列表。", None
    objs = _dedup_preserve([str(o).strip() for o in objs if str(o).strip()])
    if required and not objs:
        return False, "object 不能为空，请至少指定 1 个语义物体。", None
    invalid = [o for o in objs if o not in OBJECTS]
    if invalid:
        return False, f"不支持的物体：{', '.join(invalid)}。可选：{', '.join(OBJECTS)}", None
    return True, "", objs


def _areas_to_blocks(areas: List[str]) -> List[dict]:
    return [{"area_id": str(idx), "area_name": name, "exec_order": str(idx + 1)} for idx, name in enumerate(areas)]

def _objects_to_blocks(objs: List[str]) -> List[dict]:
    return [{"object_name": o} for o in objs]


# ---------------------------- 统一打印（发送） task_json ----------------------------
def send_task_to_device(device_id: str, task_json: dict):
    logger.info("TO {} DO {}".format(device_id, json.dumps(task_json)))
    send_rst = "success" 
    #"success" / "fail"
    return send_rst

def _log_task_json(tool: str, device_id: str, task_json: dict, status: str, reason: str | None = None) -> None:
    """
    统一打印 task_json：单行 JSON，包含工具名、设备、状态与可选失败原因。
    status: "success" / "fail"
    """
    status = send_task_to_device(device_id, task_json)
    payload = {
        "tool": tool,
        "deviceId": device_id,
        "status": status,
        "reason": reason or "",
        "task_json": task_json,
    }
    # 使用 INFO 打印成功，WARNING 打印失败；中文不转义
    line = json.dumps(payload, ensure_ascii=False)
    if status == "fail":
        logger.warning(line)
    else:
        logger.info(line)

# ---------------------------- Tools ----------------------------
# 下发成功上一行的task_json为下发到设备端的json字段，需要补充下发逻辑, 下发失败前的task_json需要返回到agent中
@mcp.tool(description="获取机器人当前时间")
def robotGetMcpTime(deviceId: str, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotGetMcpTime", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotGetMcpTime", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotGetMcpTime", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotGetMcpTime", "下发失败", "expression为空")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_json = _build_broadcast(f"当前时间：{now}", expression or "喜悦")
    _log_task_json("robotGetMcpTime", deviceId, task_json, "success")
    return _build_response(deviceId, "robotGetMcpTime", "下发成功")

@mcp.tool(description="快速建图")
def robotCreateMap(deviceId: str, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotCreateMap", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotCreateMap", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotCreateMap", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotCreateMap", "下发失败", "expression为空")
    task_json = _build_task(content or "ok，开始建图啦", expression or "喜悦", TC["Normal"], [{"task_id": "1", "task_type": TT["CreateMap"]}])
    _log_task_json("robotCreateMap", deviceId, task_json, "success")
    return _build_response(deviceId, "robotCreateMap", "下发成功")

@mcp.tool(description="返回充电桩")
def robotReturnToStation(deviceId: str, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotReturnToStation", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotReturnToStation", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotReturnToStation", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotReturnToStation", "下发失败", "expression为空")
    task_json = _build_task(content or "好的，准备回桩", expression or "喜悦", TC["Normal"],
                            [{"task_id": "1", "task_type": TT["GoToChargingStation"]}])
    _log_task_json("robotReturnToStation", deviceId, task_json, "success")
    return _build_response(deviceId, "robotReturnToStation", "下发成功")

@mcp.tool(description="安防巡检")
def robotSecurityInspection(deviceId: str, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSecurityInspection", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotSecurityInspection", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSecurityInspection", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotSecurityInspection", "下发失败", "expression为空")
    task_json = _build_task(content or "没问题，优先执行全屋巡检", expression or "喜悦", TC["Normal"],
                            [{"task_id": "1", "task_type": TT["SecurityInspection"]}])
    _log_task_json("robotSecurityInspection", deviceId, task_json, "success")
    return _build_response(deviceId, "robotSecurityInspection", "下发成功")

@mcp.tool(description="启动行人跟踪")
def robotTrackPeople(deviceId: str, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotTrackPeople", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotTrackPeople", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotTrackPeople", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotTrackPeople", "下发失败", "expression为空")
    task_json = _build_task(content or "好的，进入跟踪模式", expression or "喜悦", TC["Normal"],
                            [{"task_id": "1", "task_type": TT["TrackPerson"]}])
    _log_task_json("robotTrackPeople", deviceId, task_json, "success")
    return _build_response(deviceId, "robotTrackPeople", "下发成功")

@mcp.tool(description="直线运动（米，正前负后）")
def robotLinearMotion(deviceId: str, distance: float, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotLinearMotion", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotLinearMotion", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotLinearMotion", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotLinearMotion", "下发失败", "expression为空")
    okf, msgf, dist = _require_float("distance(米)", distance)
    if not okf:
        task_json = _build_broadcast(msgf, "担忧")
        _log_task_json("robotLinearMotion", deviceId, task_json, "fail", "distance不是数字")
        return _build_response(deviceId, "robotLinearMotion", "下发失败", "distance不是数字")
    ok, msg = _require_nonzero("distance", dist)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotLinearMotion", deviceId, task_json, "fail", "distance不能为0")
        return _build_response(deviceId, "robotLinearMotion", "下发失败", "distance不能为0")
    task_json = _build_task(content or "好的，开始动作", expression or "喜悦", TC["Normal"],
                            [{"task_id": "1", "task_type": TT["Move"], "distance": f"{dist}"}])
    _log_task_json("robotLinearMotion", deviceId, task_json, "success")
    return _build_response(deviceId, "robotLinearMotion", "下发成功")

@mcp.tool(description="原地旋转（度，正左负右）")
def robotRotation(deviceId: str, rotationAngle: float, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotRotation", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotRotation", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotRotation", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotRotation", "下发失败", "expression为空")
    okf, msgf, ang = _require_float("rotationAngle(度)", rotationAngle)
    if not okf:
        task_json = _build_broadcast(msgf, "担忧")
        _log_task_json("robotRotation", deviceId, task_json, "fail", "rotationAngle不是数字")
        return _build_response(deviceId, "robotRotation", "下发失败", "rotationAngle不是数字")
    ok, msg = _require_nonzero("rotationAngle", ang)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotRotation", deviceId, task_json, "fail", "rotationAngle不能为0")
        return _build_response(deviceId, "robotRotation", "下发失败", "rotationAngle不能为0")
    task_json = _build_task(content or "好的，开始动作", expression or "喜悦", TC["Normal"],
                            [{"task_id": "1", "task_type": TT["Rotate"], "rotation_angle": f"{ang}"}])
    _log_task_json("robotRotation", deviceId, task_json, "success")
    return _build_response(deviceId, "robotRotation", "下发成功")

@mcp.tool(description="搜索物体（可指定：区域）")
def robotSearchObject(deviceId: str,
                      targetObjects: List[str],
                      areas: Optional[List[str]] = [],
                      content: str = "",
                      expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSearchObject", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotSearchObject", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSearchObject", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotSearchObject", "下发失败", "expression为空")
    ok, msg, objs = _validate_objects(targetObjects, required=True)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSearchObject", deviceId, task_json, "fail", "object为空或非法")
        return _build_response(deviceId, "robotSearchObject", "下发失败", "object为空或非法")
    ok, msg, area_list = _validate_areas(areas, required=False)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSearchObject", deviceId, task_json, "fail", "areas为空或非法")
        return _build_response(deviceId, "robotSearchObject", "下发失败", "areas为空或非法")
    area_blocks = _areas_to_blocks(area_list) if area_list else [{"area_id": "7", "area_name": "unknown", "exec_order": "1"}]
    obj_blocks = _objects_to_blocks(objs)
    task_json = _build_task(content or "好的，准备去寻找" if area_list else "好的，我准备去找啦",
                            expression or "喜悦", TC["Normal"],
                            [{"task_id": "1", "task_type": TT["SemanticObjSearch"], "areas": area_blocks, "object": obj_blocks}])
    _log_task_json("robotSearchObject", deviceId, task_json, "success")
    return _build_response(deviceId, "robotSearchObject", "下发成功")

@mcp.tool(description="移动到物体附近（可指定：区域）")
def robotMoveToObject(deviceId: str,
                      targetObjects: List[str],
                      areas: Optional[List[str]] = list(),
                      content: str = "",
                      expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotMoveToObject", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotMoveToObject", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotMoveToObject", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotMoveToObject", "下发失败", "expression为空")
    ok, msg, objs = _validate_objects(targetObjects, required=True)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotMoveToObject", deviceId, task_json, "fail", "object为空或非法")
        return _build_response(deviceId, "robotMoveToObject", "下发失败", "object为空或非法")
    ok, msg, area_list = _validate_areas(areas, required=False)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotMoveToObject", deviceId, task_json, "fail", "areas为空或非法")
        return _build_response(deviceId, "robotMoveToObject", "下发失败", "areas为空或非法")
    task_json = _build_task(content or "好的，我准备出发啦", expression or "喜悦", TC["Normal"],
                            [{"task_id": "1", "task_type": TT["MoveToSemanticObj"],
                              "areas": _areas_to_blocks(area_list) if area_list else [],
                              "object": _objects_to_blocks(objs)}])
    _log_task_json("robotMoveToObject", deviceId, task_json, "success")
    return _build_response(deviceId, "robotMoveToObject", "下发成功")

@mcp.tool(description="取消任务")
def robotTaskCancel(deviceId: str, content: str = "", expression: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotTaskCancel", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotTaskCancel", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotTaskCancel", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotTaskCancel", "下发失败", "expression为空")
    task_json = _build_task(content or "好的，停止任务", expression or "默认", TC["Clear"], [])
    return _build_response(deviceId, "robotTaskCancel", "下发成功")


@mcp.tool(description="启动寻人功能（可指定：寻找的区域范围、待发布的通知内容、被通知人）")
def robotSearchPeople(deviceId: str, content: str = "", expression: str = "", areas: Optional[List[str]] = [], notice_word: str = "", notified_party: str = "") -> dict:
    ok, msg = _require_device(deviceId)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSearchPeople", deviceId or "", task_json, "fail", "deviceId为空")
        return _build_response(deviceId, "robotLinearMotion", "下发失败", "deviceId为空")
    ok, msg = _require_expression(expression)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSearchPeople", deviceId, task_json, "fail", "expression为空")
        return _build_response(deviceId, "robotLinearMotion", "下发失败", "expression为空")
    ok, msg, area_list = _validate_areas(areas, required=False)
    if not ok:
        task_json = _build_broadcast(msg, "担忧")
        _log_task_json("robotSearchPeople", deviceId, task_json, "fail", "areas为空或非法")
        return _build_response(deviceId, "robotMoveToObject", "下发失败", "areas为空或非法")
    
    if len(areas) < 1:
        area_list = AREAS
        
    task_json = _build_task(content or "好的，进入寻人模式", expression or "喜悦", TC["Normal"],
                                [{"task_id": "1", "task_type": TT["PersonSearch"],"areas": _areas_to_blocks(area_list) if area_list else [], "notice_word": notice_word, "notified_party": notified_party}])
    _log_task_json("robotSearchPeople", deviceId, task_json, "success")
    return _build_response(deviceId, "robotSearchPeople", "下发成功")




# ---------------------------- 入口 ----------------------------

def port_digit(port_string, default_number):
    port_number = default_number
    if port_string.isdigit():
         port_number = int(port_string)
    return port_number

if __name__ == "__main__":
    mcp_mode_by_url = os.getenv("MCP_MODE_BY_URL", "stdio")
    # 通过 环境变量 运行，适配 MCP 连接器
    if ".py" in  mcp_mode_by_url:
        mcp.run("stdio")
    elif "sse" in  mcp_mode_by_url :
        url = mcp_mode_by_url
        mcp.run(transport="sse", host=url.split("//")[-1].split("/")[0].split(":")[0], port=port_digit(url.split("//")[-1].split("/")[0].split(":")[-1], 8087), path="/{}".format(url.split("//")[-1].split("/")[-1]))
    elif "shttp" in  mcp_mode_by_url :
        url = mcp_mode_by_url
        mcp.run(transport="streamable-http", host=url.split("//")[-1].split("/")[0].split(":")[0], port=port_digit(url.split("//")[-1].split("/")[0].split(":")[-1], 8088), path="/{}".format(url.split("//")[-1].split("/")[-1]))


