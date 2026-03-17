from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import yaml
import subprocess

# Import internal modules using relative imports
from .llm import generate_response
from .actions import perform_action
from .memory import memory_manager

# Load config
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {
        'server': {'host': '127.0.0.1', 'port': 8000},
        'model': {'name': 'llama-3.2.1'},
        'db': {'host': 'localhost', 'port': 5432, 'name': 'openclaw_mvp_db', 'user': 'openclaw_user', 'password': 'your_secure_db_password'},
        'redis': {'host': 'localhost', 'port': 6379},
        'safety': {'confirm_sensitive_actions': True}
    }

config = load_config()
server_config = config.get('server', {})
model_config = config.get('model', {})
action_config = config.get('safety', {})

app = FastAPI(title="OpenClaw MVP Backend", version="0.1.0")

# Serve UI statically
app.mount("/ui", StaticFiles(directory=os.path.join(os.path.dirname(__file__), '..', 'ui')), name="ui")

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/ui/index.html")

class UserQuery(BaseModel):
    text: str
    session_id: str = "default_session"

class ChatResponse(BaseModel):
    user_text: str
    agent_response: str | None = None
    action_performed: str | None = None
    action_result: str | None = None
    error: str | None = None

class HistoryResponse(BaseModel):
    logs: list

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(query: UserQuery):
    user_text = query.text
    session_id = query.session_id

    try:
        # 1) LLM response (MVP: just text plus optional action)
        ai_text_raw = generate_response(user_text)

        ai_response = ai_text_raw
        action_performed = None
        action_result = None

        if "ACTION:" in ai_text_raw:
            action_part = ai_text_raw.split("ACTION:", 1)[1].strip()
            parts = action_part.split()
            if parts:
                action_name = parts[0]
                action_args_str = " ".join(parts[1:])

                action_kwargs = {}
                if action_name == "open_app":
                    if action_args_str: action_kwargs['app_name'] = action_args_str
                elif action_name == "type_text":
                    if action_args_str: action_kwargs['text'] = action_args_str
                elif action_name == "read_file":
                    if action_args_str: action_kwargs['file_path'] = action_args_str
                elif action_name == "list_files":
                    if action_args_str: action_kwargs['folder_path'] = action_args_str
                else:
                    action_name = None

                if action_name:
                    ai_response = ai_text_raw.split("ACTION:")[0].strip() or f"Executing action: {action_name}"
                    action_result_data = perform_action(action_name, **action_kwargs)
                    action_performed = f"{action_name} ({action_kwargs})"
                    action_result = str(action_result_data)

                    if action_result_data.get("status") == "success":
                        if action_name not in ai_response:
                            ai_response += f"\n{action_result_data.get('message', '')}"
                    else:
                        ai_response = f"Error performing action: {action_result_data.get('message', 'Unknown error')}."
                        action_result = str(action_result_data)

        # 2) Log to memory
        memory_manager.log_conversation_turn(
            user_text=user_text,
            ai_response=ai_response,
            action_performed=action_performed,
            action_result=action_result
        )

        return ChatResponse(
            user_text=user_text,
            agent_response=ai_response,
            action_performed=action_performed,
            action_result=action_result
        )
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        memory_manager.log_conversation_turn(
            user_text=user_text,
            ai_response=None,
            action_performed="error",
            action_result=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/history", response_model=HistoryResponse)
async def get_history_endpoint():
    try:
        logs = memory_manager.get_recent_logs(limit=20)
        return HistoryResponse(logs=logs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@app.get("/status")
async def status_endpoint():
    db_status = "Connected" if memory_manager.conn else "Disconnected"
    redis_status = "Connected" if memory_manager.redis_client else "Disconnected"

    model_name = model_config.get('name', 'N/A')

    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
        ollama_status = f"Ollama CLI found (Model: {model_name})"
    except FileNotFoundError:
        ollama_status = "Ollama not found"
    except Exception:
        ollama_status = "Ollama check failed"

    return {
        "message": "OpenClaw MVP Backend Status",
        "server_host": server_config.get('host', '127.0.0.1'),
        "server_port": server_config.get('port', 8000),
        "llm": {"provider": config.get('model', {}).get('provider', 'ollama'), "model_name": model_name},
        "database": {"status": db_status, "name": memory_manager.db_config.get('name', 'N/A'), "host": memory_manager.db_config.get('host', 'N/A'), "port": memory_manager.db_config.get('port', 'N/A')},
        "redis": {"status": redis_status, "host": memory_manager.redis_config.get('host', 'N/A'), "port": memory_manager.redis_config.get('port', 'N/A')},
        "ollama_service": ollama_status
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server on {server_config.get('host','127.0.0.1')}:{server_config.get('port', 8000)}")
    uvicorn.run(app, host=server_config.get('host', '127.0.0.1'), port=server_config.get('port', 8000))
