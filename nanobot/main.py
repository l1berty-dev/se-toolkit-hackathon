import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI(title="LMS Query Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Пытаемся подключиться к ИИ (настройки из .env)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "no-key"),
    base_url=os.getenv("OPENAI_API_BASE", "http://qwen-proxy:8080/v1")
)

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message", "").lower()
        
        # 1. Попытка использовать настоящий ИИ
        try:
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "coder-model"),
                messages=[{"role": "user", "content": user_msg}],
                timeout=3.0
            )
            return {"response": response.choices[0].message.content}
        except Exception as e:
            # 2. FALLBACK: Если ИИ не работает, выдаем данные напрямую
            print(f"AI not available, using Direct Mode. Error: {str(e)}")
            
            if "deadline" in user_msg or "assignment" in user_msg or "what" in user_msg:
                resp = requests.get("http://backend:8000/assignments")
                items = resp.json()
                res = "📅 **[Direct Mode] Upcoming Deadlines:**\n"
                for i in items:
                    res += f"- {i['title']} ({i['course_name']}): {i['deadline']}\n"
                return {"response": res}
                
            if "grade" in user_msg or "score" in user_msg:
                resp = requests.get("http://backend:8000/grades")
                items = resp.json()
                res = "🎓 **[Direct Mode] Your Grades:**\n"
                for i in items:
                    res += f"- {i['title']} ({i['course_name']}): {i['score']}/{i['max_score']}\n"
                return {"response": res}
                
            return {"response": "I'm currently in **Direct Data Mode** (AI is offline). Ask me about your **deadlines** or **grades**!"}
            
    except Exception as fatal_e:
        return {"response": f"System Error: {str(fatal_e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
