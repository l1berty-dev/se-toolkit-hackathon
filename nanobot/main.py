import os
import json
import importlib.util
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from typing import List, Dict

app = FastAPI(title="LMS Query Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к Qwen через прокси
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE")
)

MODEL_NAME = os.getenv("LLM_MODEL", "coder-model")
TOOLS_DIR = "/app/agents/tools"

def load_tools():
    tools = []
    if not os.path.exists(TOOLS_DIR):
        return tools
    for filename in os.listdir(TOOLS_DIR):
        if filename.endswith(".py"):
            tool_name = filename[:-3]
            spec = importlib.util.spec_from_file_location(tool_name, os.path.join(TOOLS_DIR, filename))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, tool_name):
                func = getattr(module, tool_name)
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": func.__doc__.strip() if func.__doc__ else "Access LMS data",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    "call": func
                })
    return tools

TOOLS_REGISTRY = load_tools()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_msg = data.get("message", "")
    
    messages = [
        {"role": "system", "content": "You are a helpful academic assistant. Use tools to answer questions about deadlines and grades."},
        {"role": "user", "content": user_msg}
    ]
    
    try:
        api_tools = [{"type": "function", "function": t["function"]} for t in TOOLS_REGISTRY]
        
        # 1. Запрос к ИИ
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=api_tools,
            tool_choice="auto"
        )
        
        msg = response.choices[0].message
        
        # 2. Вызов инструментов
        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                tool_func = next(t for t in TOOLS_REGISTRY if t["function"]["name"] == tool_call.function.name)
                result = tool_func["call"]()
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
            
            # 3. Финальный ответ
            final_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages
            )
            return {"response": final_response.choices[0].message.content}
        
        return {"response": msg.content}
    except Exception as e:
        return {"response": f"AI Service Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
