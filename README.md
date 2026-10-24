# Everyday AI — a simple chat assistant

A small, repository-ready Python project: FastAPI serves a responsive HTML/CSS/JavaScript chat interface and forwards conversations to a locally running Ollama model. No paid API key, LangChain, database, or frontend build step is required.

## What it does

- Polite, clear answers guided by an editable system prompt.
- Follow-up questions with recent conversation context (up to ten preceding exchanges, reduced when the character budget is reached).
- New-chat button, example questions, busy indicator, and actionable connection/model errors.
- Separate history per browser tab, in memory only; reload clears it.
- Input validation, timeouts, plain-text rendering, API tests, and GitHub Actions.

The assistant has no live search, document retrieval, tools, or permanent memory. Answer quality depends on the model and question; it cannot guarantee correct or satisfying answers. Responses appear when generation completes rather than token by token. Long answers can stop at the configured output limit; ask the assistant to continue.

## Quick start on Windows (PowerShell)

Prerequisites: Python 3.11+ and an installed, running Ollama. Open the extracted project folder in VS Code or PyCharm; use its terminal.

```powershell
ollama pull qwen3:4b
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Keep the terminal running. Stop with Ctrl+C. If `ollama` is unrecognized, reopen your terminal after installing Ollama and check its PATH. If Ollama is not running, open the Ollama app or run `ollama serve` in another terminal. Do not start a second Ollama server if one is already listening.

For macOS/Linux:

```bash
ollama pull qwen3:4b
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The first response may be slow while the model loads. Hardware affects response speed. This app disables thinking output for the default Qwen model and caps generation at 768 tokens.

## Configure

Set environment variables **before** launching the server. `.env.example` documents available values; it is not automatically loaded.

```powershell
$env:OLLAMA_URL = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "qwen3:4b"
```

On Linux/macOS use `export OLLAMA_MODEL="qwen3:4b"`. Download any replacement model with `ollama pull MODEL_NAME`. The app sends `think: false`; adapt this setting if your replacement model does not support it.

Edit `SYSTEM_PROMPT` in `app/main.py` to adjust the assistant's tone and scope. Adjust `num_predict`, `num_ctx`, and timeout there if needed. Character limits are not exact token limits; multilingual text and long conversations may exceed the model context budget. Start a new chat if the model loses context.

## Project structure

```text
app/main.py                FastAPI routes, validation, model adapter, prompt
app/static/index.html      Chat page
app/static/style.css       Responsive styling
app/static/chat.js         Chat state and API requests
tests/test_chat.py         Offline API and provider-adapter tests
.github/workflows/tests.yml GitHub CI
Dockerfile                 Optional container for the Python app
requirements.txt           Compatible dependency ranges
.env.example               Environment variable reference
```

Flow: browser → POST /api/chat → FastAPI → Ollama /api/chat → answer → browser.

The backend has no shared conversation store. Each request supplies its own history. No messages are deliberately written to disk by this app; model-server and hosting logs are separate. The public API accepts only user/assistant messages and adds the system prompt on the server. Prompt instructions are behavioral guidance, not a security boundary.

## API

Interactive API docs: **http://127.0.0.1:8000/docs**. `/health` checks the Python process only, not model readiness.

Example body for `POST /api/chat`:

```json
{"messages":[{"role":"user","content":"Explain Python decorators with a simple example."}]}
```

Response:

```json
{"reply":"A decorator is ..."}
```

History must alternate user/assistant, starting and ending with user. Maximum 21 messages, 8,000 characters per message, 24,000 characters total. The browser automatically removes older complete turns to fit those limits.

## Tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests mock the model server and need no GPU or Ollama installation. A real-model smoke test is separate: start Ollama and the app, ask a question, then ask a follow-up referring to it. Try New chat and confirm the previous conversation disappears.

## Push to your GitHub repository

Create an empty repository on GitHub, then run these from the folder containing this README. Replace the placeholder URL with your repository URL.

```bash
git init
git add .
git commit -m "Add simple Ollama AI chat assistant"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-assistant.git
git push -u origin main
```

If using an existing repository, copy the project files into it and use its current Git setup. Do not commit `.venv` or secrets. requirements.txt provides compatible ranges. requirements-lock.txt records the exact versions used for the passing tests; install it with pip install -r requirements-lock.txt to reproduce that environment (Python 3.12).

**GitHub stores this code; GitHub Pages cannot run the Python backend or Ollama.** To host a working assistant, run both on a suitable server with adequate memory/CPU/GPU. A cloud server cannot reach Ollama on your laptop using `localhost`: configure a private reachable model endpoint instead.

## Optional Docker deployment

Run Ollama on the Docker host and download the model first. Build the app:

```bash
docker build -t everyday-ai .
```

On Docker Desktop (Windows/macOS), run:

```bash
docker run --rm -p 127.0.0.1:8000:8000 -e OLLAMA_URL=http://host.docker.internal:11434 -e OLLAMA_MODEL=qwen3:4b everyday-ai
```

Ollama must accept connections from the container. Depending on host configuration, its loopback-only default may need changing. If changing its bind address, use a firewall to restrict access to your trusted host/container network. Do not expose its unauthenticated API directly to the internet.

On Linux, a local alternative is:

```bash
docker run --rm --network host -e OLLAMA_URL=http://127.0.0.1:11434 everyday-ai
```

Host networking on Linux binds this app on all host interfaces at port 8000, so restrict it with a firewall. The Docker image contains the app only; it does not contain Ollama or model weights. Container build and real-model operation should be validated on your deployment machine.

## Before allowing public users

This starter is intended for local/private use. Add authentication, per-user rate limits, concurrency/queue limits, request-size limits at your reverse proxy, HTTPS, and appropriate privacy controls before public hosting. The current input limits are validated after JSON parsing and are not a transport-level body-size limit. Keep Ollama private. It has no user accounts, abuse monitoring, durable chat storage, or production capacity management.

For a small private server, the Python process can be started with:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use a process manager and an HTTPS reverse proxy when hosting. Do not use `--reload` in production.

## Official references

- https://docs.ollama.com/api/chat
- https://fastapi.tiangolo.com/deployment/manually/
