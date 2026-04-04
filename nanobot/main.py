import os
import requests
import json
import uvicorn
import traceback
import logging
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

def get_performance_data():
    try:
        resp = requests.get(f"{BACKEND_URL}/courses/performance")
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_performance_data",
            "description": "Get weighted grades, thresholds, and upcoming assignments for calculations.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

SYSTEM_PROMPT = """You are a professional Academic Advisor. 
Style: Logical, clear, and concise. 
Format: DO NOT use large headers (#). Use **Bold** for emphasis and bullet points.

Response Structure:
**Current Status:** [1-sentence summary of course performance]
**The Goal:** [Threshold for the target grade]
**Calculation:** `[Required = (Threshold - Current) / Weight]`
**Requirement:** **[Score]%** on [Assignment]
**Expert Advice:** [1 brief sentence of encouragement or strategy]
"""

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message", "")

        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "coder-model"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            tools=tools,
            tool_choice="auto"
        )

        assistant_msg = response.choices[0].message
        
        if assistant_msg.tool_calls:
            results_messages = []
            tool_calls_data = []
            for tc in assistant_msg.tool_calls:
                tool_calls_data.append({"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}})
                if tc.function.name == "get_performance_data":
                    res = get_performance_data()
                else: res = "Unknown tool"
                results_messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": json.dumps(res)})
            
            final_response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "coder-model"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg.content or "", "tool_calls": tool_calls_data},
                    *results_messages
                ]
            )
            return {"response": final_response.choices[0].message.content}
        
        return {"response": assistant_msg.content}
    except Exception as e:
        return {"response": f"**Advisor Error:** {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
