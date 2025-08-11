from fastapi import FastAPI
from fastmcp import FastMCP
import uuid
import logging
from datetime import datetime
from typing import List

# ---------------------------- 初始化 ----------------------------
app = FastAPI()
mcp = FastMCP.from_fastapi(app=app)
logger = logging.getLogger("luna_mcp")
logging.basicConfig(level=logging.DEBUG)

# ---------------------------- 语义枚举 ----------------------------
AREAS = ["卧室", "客厅", "书房", "厨房", "餐厅", "卫生间", "阳台", "走廊", "unknown"]
OBJECTS = [
    "鞋子", "垃圾桶", "底座", "线团", "插棑", "猫", "狗", "方桌", "圆桌", "体重称", "充电桩", "钥匙",
    "椅子", "沙发", "床", "电视柜", "冰箱", "电视", "洗衣机", "电风扇", "遥控器", "鞋柜"
]

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
        "structuredContent": {
            "deviceId": device_id,
            "results": [
                {
                    "taskType": task_type,
                    "status": status,
                    "detail": detail
                }
            ]
        }
    }

def _validate_areas(areas: List[str] | None) -> tuple[bool, str]:
    if not areas:
        return True, ""
    invalid = [a for a in areas if a not in AREAS]
    if invalid:
        return False, f"不支持的区域: {', '.join(invalid)}"
    return True, ""

def _validate_objects(objs: List[str] | None) -> tuple[bool, str]:
    if not objs:
        return True, ""
    invalid = [o for o in objs if o not in OBJECTS]
    if invalid:
        return False, f"不支持的物体: {', '.join(invalid)}"
    return True, ""

# ---------------------------- 标准 Tools（10 个） ----------------------------

@mcp.tool(description="获取机器人当前时间")
def robotGetMcpTime(deviceId: str, content: str = "", expression: str = "") -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"当前时间：{now}"
    return _build_response(deviceId, "robotGetMcpTime", "下发成功", msg)

@mcp.tool(description="快速建图，构建初始地图信息")
def robotCreateMap(deviceId: str, content: str = "", expression: str = "") -> dict:
    return _build_response(deviceId, "robotCreateMap", "下发成功", "已开始快速建图")

@mcp.tool(description="返回充电桩，自动对接充电")
def robotReturnToStation(deviceId: str, content: str = "", expression: str = "") -> dict:
    return _build_response(deviceId, "robotReturnToStation", "下发成功", "返回充电桩中")

@mcp.tool(description="启动全屋安防巡检任务")
def robotSecurityInspection(deviceId: str, content: str = "", expression: str = "") -> dict:
    return _build_response(deviceId, "robotSecurityInspection", "下发成功", "已启动全屋巡检")

@mcp.tool(description="跟踪指定目标人物")
def robotTrackPeople(deviceId: str, content: str = "", expression: str = "") -> dict:
    return _build_response(deviceId, "robotTrackPeople", "下发成功", "开始人物跟踪")

@mcp.tool(description="执行直线运动，单位米；正为前进，负为后退")
def robotLinearMotion(deviceId: str, distance: float, content: str = "", expression: str = "") -> dict:
    try:
        d = float(distance)
    except Exception:
        return _build_response(deviceId, "robotLinearMotion", "参数错误", "distance 需为数字", "PARAM_MISSING")
    return _build_response(deviceId, "robotLinearMotion", "下发成功", f"直线运动 {d} 米")

@mcp.tool(description="执行原地旋转动作，单位度；正为左转，负为右转")
def robotRotation(deviceId: str, rotationAngle: float, content: str = "", expression: str = "") -> dict:
    try:
        ang = float(rotationAngle)
    except Exception:
        return _build_response(deviceId, "robotRotation", "参数错误", "rotationAngle 需为数字", "PARAM_MISSING")
    return _build_response(deviceId, "robotRotation", "下发成功", f"旋转 {ang} 度")

@mcp.tool(description="搜索指定物体，可选搜索区域")
def robotSearchObject(deviceId: str,
                      targetObjects: List[str],
                      areas: List[str] | None = None,
                      content: str = "",
                      expression: str = "") -> dict:
    ok, msg = _validate_objects(targetObjects)
    if not ok:
        return _build_response(deviceId, "robotSearchObject", "参数错误", msg, "OBJECT_INVALID")
    ok, msg = _validate_areas(areas)
    if not ok:
        return _build_response(deviceId, "robotSearchObject", "参数错误", msg, "AREA_INVALID")
    a = f" 在区域 {areas}" if areas else ""
    return _build_response(deviceId, "robotSearchObject", "下发成功", f"搜索物体 {targetObjects}{a}")

@mcp.tool(description="移动到指定物体附近，可选区域")
def robotMoveToObject(deviceId: str,
                      targetObjects: List[str],
                      areas: List[str] | None = None,
                      content: str = "",
                      expression: str = "") -> dict:
    ok, msg = _validate_objects(targetObjects)
    if not ok:
        return _build_response(deviceId, "robotMoveToObject", "参数错误", msg, "OBJECT_INVALID")
    ok, msg = _validate_areas(areas)
    if not ok:
        return _build_response(deviceId, "robotMoveToObject", "参数错误", msg, "AREA_INVALID")
    a = f" 在区域 {areas}" if areas else ""
    return _build_response(deviceId, "robotMoveToObject", "下发成功", f"前往物体 {targetObjects}{a}")

@mcp.tool(description="取消当前执行中的任务")
def robotTaskCancel(deviceId: str, content: str = "", expression: str = "") -> dict:
    return _build_response(deviceId, "robotTaskCancel", "下发成功", "已取消当前任务")

# ---------------------------- 入口 ----------------------------
if __name__ == "__main__":
    # 通过 stdio 运行，适配 MCP 连接器
    mcp.run(transport="stdio")
