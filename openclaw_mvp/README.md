# OpenClaw MVP (Native macOS, no Docker)

This is a minimal, native MVP for a local macOS AI assistant named OpenClaw. It runs entirely on your Mac, with local LLM (Ollama), local memory (PostgreSQL + Redis), and a tiny web UI.

Getting started (quick version)
- Prereqs:
  - Python 3.12+ and a virtualenv (ai-dev)
  - Ollama running with a local model (e.g., llama-3.2.1)
  - PostgreSQL and Redis running
- Install and run:
  1) Create the repo structure (as provided) and place the files
  2) Activate venv: source ~/venvs/ai-dev/bin/activate
  3) Install deps: pip install -r backend/requirements.txt
  4) Start the backend: ./run.sh
  5) Open http://127.0.0.1:8000/ (UI)

What this MVP includes
- Local-only macOS assistant via chat
- Local LLM backend via Ollama
- Simple actions: open apps, read files, type text, list files
- Local memory with PostgreSQL + Redis
- Minimal UI (HTML/JS) served by FastAPI

What to improve next
- Robust action parsing from LLM output
- UI polish (React/Vue or server-rendered)
- Voice I/O with Whisper and pyttsx3
- LangChain orchestration for richer planning and tools
- Stronger safety prompts and explicit user confirmations for sensitive actions
