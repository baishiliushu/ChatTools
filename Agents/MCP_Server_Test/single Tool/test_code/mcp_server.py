from fastapi import FastAPI
from fastmcp import FastMCP
import random
import logging

app = FastAPI()
mcp = FastMCP.from_fastapi(app=app)
logger = logging.getLogger("luna_mcp")
logging.basicConfig(level=logging.DEBUG)

# ---------------------------- Tool: controlImdRobot ----------------------------
@mcp.tool(description="控制机器人底盘任务指令集合。支持多个任务组合，包括建图、巡检、旋转、移动、寻物等。")
def controlImdRobot(
    deviceId: str,
    content: str = "",
    expression: str = "默认",
    robotTaskControl: str = "执行",
    robotTaskLists: list = []
):
    """
    :param deviceId: 机器人设备 ID
    :param content: 播报内容
    :param expression: 表情
    :param robotTaskControl: 执行控制（执行/取消）
    :param robotTaskLists: 任务队列
    :return: dict
    """
    session_id = str(random.randint(1000, 9999))
    return {
        "content": content,
        "expression": expression,
        "session_id": session_id,
        "type": "3",
        "task_cont": "1" if robotTaskControl == "执行" else "2",
        "tasks": robotTaskLists
    }

if __name__ == "__main__":
    mcp.run(transport='stdio')

