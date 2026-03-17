import subprocess
import os
import yaml
import pyautogui
import time

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

config = load_config()
safety_config = config.get('safety', {})

def is_sensitive_action(action_name: str) -> bool:
    sensitive_actions = ['type_text', 'delete_file', 'run_shell_command']
    return action_name in sensitive_actions

def perform_action(action_name: str, **kwargs) -> dict:
    """Execute a macOS action. Returns a dict with status and message."""
    if safety_config.get('confirm_sensitive_actions', True) and is_sensitive_action(action_name):
        print(f"SECURITY: Auto-approving sensitive action '{action_name}' (MVP).")

    try:
        if action_name == "open_app":
            app_name = kwargs.get("app_name")
            if not app_name:
                return {"status": "error", "message": "Missing 'app_name' for open_app."}
            subprocess.run(["open", "-a", app_name], check=True)
            return {"status": "success", "message": f"Opened {app_name}."}

        elif action_name == "type_text":
            text_to_type = kwargs.get("text")
            if text_to_type is None:
                return {"status": "error", "message": "Missing 'text' for type_text."}
            time.sleep(0.2)
            pyautogui.write(text_to_type, interval=0.05)
            return {"status": "success", "message": f"Typed: {text_to_type[:30]}{'...' if len(text_to_type) > 30 else ''}"}

        elif action_name == "read_file":
            file_path = kwargs.get("file_path")
            if not file_path:
                return {"status": "error", "message": "Missing 'file_path' for read_file."}
            if not file_path.startswith(os.path.expanduser("~")):
                return {"status": "denied", "message": "Access to this path is restricted."}
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return {"status": "success", "message": f"Content of {file_path}:\n{content[:500]}{'...' if len(content) > 500 else ''}"}

        elif action_name == "list_files":
            folder_path = kwargs.get("folder_path", ".")
            if not os.path.isdir(folder_path):
                return {"status": "error", "message": f"'{folder_path}' is not a directory."}
            files = os.listdir(folder_path)
            preview = ", ".join(files[:10])
            return {"status": "success", "message": f"Files in {folder_path}: {preview}{'...' if len(files) > 10 else ''}"}

        else:
            return {"status": "error", "message": f"Unknown action '{action_name}'."}
    except FileNotFoundError:
        return {"status": "error", "message": f"Resource not found for action '{action_name}'."}
    except PermissionError:
        return {"status": "error", "message": f"Permission denied for action '{action_name}'. Review macOS permissions."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Command failed for '{action_name}': {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error in action '{action_name}': {str(e)}"}

def confirm_action_request(action_name: str, **kwargs) -> bool:
    """Placeholder confirmation for MVP. Always return True for now."""
    print(f"SECURITY ALERT (MVP): Approve action {action_name} with args {kwargs}")
    return True
