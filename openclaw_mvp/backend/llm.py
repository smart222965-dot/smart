import subprocess
import yaml
import os
from dotenv import load_dotenv  # type: ignore

load_dotenv()  # Load .env if present

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            cfg = yaml.safe_load(f)
    else:
        cfg = {}
    # Environment overrides
    cfg['model'] = {
        'name': os.getenv('OLLAMA_MODEL', cfg.get('model', {}).get('name', 'llama-3.2.1'))
    }
    cfg['db'] = {
        'host': os.getenv('DB_HOST', cfg.get('db', {}).get('host', 'localhost')),
        'port': int(os.getenv('DB_PORT', cfg.get('db', {}).get('port', 5432))),
        'name': os.getenv('DB_NAME', cfg.get('db', {}).get('name', 'openclaw_mvp_db')),
        'user': os.getenv('DB_USER', cfg.get('db', {}).get('user', 'openclaw_user')),
        'password': os.getenv('DB_PASSWORD', cfg.get('db', {}).get('password', 'your_secure_db_password')),
    }
    return cfg

config = load_config()

def generate_response(prompt: str) -> str:
    """Generate response from local Ollama model (simple MVP wrapper)."""
    model_name = config['model']['name']
    templated_prompt = f"""
You are a helpful macOS assistant named OpenClaw. Respond to the user's request.
If the request requires an action (like opening an app or typing text), indicate it with "ACTION: [action_name] [arguments]".
Otherwise, respond directly in text.

User: {prompt}
OpenClaw: """
    try:
        cmd = ["ollama", "run", model_name, "--prompt", templated_prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = result.stdout.strip()
        # Lightweight cleanup
        if response.startswith("OpenClaw:"):
            response = response[len("OpenClaw:"):].strip()
        return response
    except FileNotFoundError:
        return "ERROR: 'ollama' command not found. Is Ollama installed and in your PATH?"
    except subprocess.CalledProcessError as e:
        return f"ERROR: Ollama failed. {e.stderr.strip()}"
    except Exception as e:
        return f"ERROR: LLM error: {str(e)}"
