from fastapi import FastAPI
from openai import OpenAI
import sys

# 强制使用 UTF-8（避免 Windows 编码问题）
sys.stdout.reconfigure(encoding='utf-8')

app = FastAPI()

# 👉 用你自己的 key（注意不要再泄露）
client = OpenAI(
    api_key="sk-db253c0dc8624d999879e2b15e0dd788",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 👉 全局数据（很重要）
chat_history = []
logs = []

# ================= 基础接口 =================

@app.get("/")
def read_root():
    return {"msg": "Hello AI world"}

@app.get("/add")
def add(a: int, b: int):
    return {"result": a + b}

@app.get("/user")
def get_user(name: str, age: int):
    return {
        "name": name,
        "age": age,
        "msg": f"你好 {name}"
    }

# ================= AI聊天 =================

@app.get("/chat")
def chat(msg: str):
    try:
        # 记录用户输入
        chat_history.append({"role": "user", "content": msg})

        response = client.chat.completions.create(
            model="qwen3.6-plus",
            messages=chat_history
        )

        reply = str(response.choices[0].message.content)

        # 记录AI回复
        chat_history.append({"role": "assistant", "content": reply})

        return {"reply": reply}

    except Exception as e:
        return {
            "error_type": str(type(e)),
            "error_msg": repr(e)
        }

# ================= 学习记录 =================

@app.get("/log")
def add_log(content: str):
    logs.append(content)
    return {"msg": "记录成功", "logs": logs}