import os
import requests
import json
import uvicorn
import traceback
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LMS Pro Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY", "my-secret-qwen-key"),
    base_url=os.getenv("LLM_API_BASE", "http://localhost:42005/v1")
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def _format_time_left(deadline_str: str) -> str:
    if not deadline_str:
        return "no deadline"
    try:
        clean_date = deadline_str.replace(" ", "T")
        dl = datetime.fromisoformat(clean_date)
        now = datetime.now()
        if dl.tzinfo is not None:
            dl = dl.replace(tzinfo=None)
        diff = (dl - now).total_seconds()
        if diff < 0: return "overdue"
        days = int(diff // 86400)
        hours = int((diff % 86400) // 3600)
        return f"{days}d {hours}h left" if days > 0 else f"{hours}h left"
    except: return deadline_str

def get_performance_data():
    try:
        resp = requests.get(f"{BACKEND_URL}/courses/performance")
        data = resp.json()
        if isinstance(data, list):
            for c in data:
                for a in c.get("assignments", []):
                    a["time_left"] = _format_time_left(a.get("deadline"))
        return data
    except Exception as e: return {"error": str(e)}

def get_deadlines():
    try:
        resp = requests.get(f"{BACKEND_URL}/deadlines")
        data = resp.json()
        if isinstance(data, list):
            for d in data: d["time_left"] = _format_time_left(d.get("deadline"))
        return data
    except Exception as e: return {"error": str(e)}

def get_grades():
    try:
        resp = requests.get(f"{BACKEND_URL}/grades")
        return resp.json()
    except Exception as e: return {"error": str(e)}

TOOLS = [
    {"type": "function", "function": {"name": "get_performance_data", "description": "Get courses, grades, and thresholds."}},
    {"type": "function", "function": {"name": "get_deadlines", "description": "Get all upcoming deadlines."}},
    {"type": "function", "function": {"name": "get_grades", "description": "Get all recorded grades."}}
]

SYSTEM_PROMPT = """You are a minimalist Academic Advisor. Use tools to fetch data.
Respond strictly in English. NO conversational filler. NO large headers (###). NO bullet points (- or *).
Use only one of these templates based on user intent:

**ACADEMIC FORECAST: [Course Name]** 🔮

**Target**: [Grade + %]

**Current**: [Score %]

**Required**: [Score %]

**Math**: (Threshold - Current) / RemainingWeight

**Advice**: [1 sentence] 💡

**DEADLINES OVERVIEW** 📅

**Course**: [Course Name]

**Upcoming**: [Assignment 1 (Date), Assignment 2 (Date)...]

**Status**: [e.g., 3 pending, 1 overdue]

**Tip**: [1 sentence] ⏳

**GRADES REPORT** 📝

**Course**: [Course Name]

**Scores**: [Assignment 1: Score%, Assignment 2: Score%...]

**Current Average**: [Weighted %]

**Standing**: [Current Grade Letter]

**PRIORITY LIST** ⚡

**Top Task**: [Assignment Name] ([Deadline]) 📅

**Impact**: [Course Name] ([Weight %])

**Next Step**: [1 sentence advice] 🚀

**PROGRESS STATUS** 📊

**Overall**: [Summary of all courses]

**Best**: [Course Name] 🏆

**Warning**: [Course Name with overdue or low score] ⚠️

**Tip**: [1 sentence strategy] 🎯

Rules:
1. Always start with the Template Title, then a blank line.
2. Every field label MUST be **Bold**.
3. Use exactly ONE empty line between each field for readability.
4. If asked for a joke, it MUST be related to academia, students, or professors.
5. If non-academic and not a joke, say: "I only provide academic advice."
6. Always respond in English.
"""

def run_agent_loop(user_msg: str):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}]
    for _ in range(5):
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "coder-model"),
            messages=messages, tools=TOOLS, tool_choice="auto", temperature=0.1
        )
        assistant_msg = response.choices[0].message
        msg_to_append = {"role": "assistant", "content": assistant_msg.content or ""}
        if assistant_msg.tool_calls:
            msg_to_append["tool_calls"] = [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in assistant_msg.tool_calls]
        messages.append(msg_to_append)

        if not assistant_msg.tool_calls:
            return assistant_msg.content or "I processed your request but have no specific comments. How else can I help?"

        for tool_call in assistant_msg.tool_calls:
            fname = tool_call.function.name
            if fname == "get_performance_data": res = get_performance_data()
            elif fname == "get_deadlines": res = get_deadlines()
            elif fname == "get_grades": res = get_grades()
            else: res = {"error": "Unknown tool"}
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": fname, "content": json.dumps(res)})
    return "Limit reached."

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        ans = run_agent_loop(data.get("message", ""))
        return {"response": ans}
    except Exception as e: return {"response": f"**Advisor Error:** {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
