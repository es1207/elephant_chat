import json
import os
import logging
import time
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import sys

# UTF-8（Windows）
sys.stdout.reconfigure(encoding='utf-8')

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= 日志 =================
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ================= API =================
client = OpenAI(
    api_key="sk-db253c0dc8624d999879e2b15e0dd788",  # ← 替换
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ================= 数据 =================
USER_FILE = "users.json"
DATA_FILE = "chat_data.json"

if os.path.exists(USER_FILE):
    with open(USER_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        user_histories = json.load(f)
else:
    user_histories = {}

# ================= 错误体系（Day17核心） =================
class ErrorCode:
    SUCCESS = 0
    INVALID_PARAM = 1001
    TOO_FAST = 1002
    SERVER_ERROR = 2000

def success(data=None):
    return {
        "code": 0,
        "msg": "success",
        "data": data
    }

def error(code, msg):
    return {
        "code": code,
        "msg": msg,
        "data": None
    }

# ================= 请求模型 =================
class ChatRequest(BaseModel):
    msg: str
    user_id: str

# ================= 限流 =================
last_request_time = {}

# ================= 接口 =================

@app.get("/")
def root():
    return success({"msg": "OK"})

# 登录
@app.get("/login")
def login(username: str):
    if username not in users:
        users[username] = {"msg": "new user"}

        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

    return success({"user_id": username})

# 聊天（Day12-17综合）
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        msg = req.msg
        user_id = req.user_id

        if not msg:
            return error(ErrorCode.INVALID_PARAM, "msg不能为空")

        # 限流（Day16）
        now = time.time()
        if user_id in last_request_time:
            if now - last_request_time[user_id] < 2:
                return error(ErrorCode.TOO_FAST, "请求太快了")
        last_request_time[user_id] = now

        logging.info(f"user={user_id}, msg={msg}")

        if user_id not in user_histories:
            user_histories[user_id] = []

        history = user_histories[user_id]

        # 上下文裁剪（Day15）
        MAX_HISTORY = 10
        history = history[-MAX_HISTORY:]

        history.append({"role": "user", "content": msg})

        response = client.chat.completions.create(
            model="qwen3.6-plus",
            messages=history
        )

        reply = str(response.choices[0].message.content)

        history.append({"role": "assistant", "content": reply})

        user_histories[user_id] = history

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(user_histories, f, ensure_ascii=False, indent=2)

        return success({"reply": reply})

    except Exception as e:
        logging.error(str(e))
        return error(ErrorCode.SERVER_ERROR, "服务器异常")

# 历史
@app.get("/history")
def history(user_id: str):
    return success({"history": user_histories.get(user_id, [])})

# 清空
@app.get("/clear")
def clear(user_id: str):
    user_histories[user_id] = []

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_histories, f, ensure_ascii=False, indent=2)

    return success({"msg": "已清空"})