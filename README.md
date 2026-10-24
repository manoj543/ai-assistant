# AI Assistant — Render + Groq

A FastAPI chat assistant with a browser UI, Groq for online inference, and optional
Ollama for local development. Docker runs only the web app; no model download or
GPU is required on Render. Includes a GitHub Pages chat page and tested-commit
Render deploy hook workflow.

## 1. Put the project in GitHub

Extract the ZIP. Copy the **contents** of `ai-assistant-render-groq/` to the root
of your backend GitHub repository. Include `.github/`, `Dockerfile`,
`render.yaml`, and `requirements-lock.txt`. Do not commit real keys or `.env`.
The workflow assumes your deployment branch is `main`.

## 2. Create a Groq key

Create/sign in to https://console.groq.com and generate an API key at
https://console.groq.com/keys. Keep your account on the Free plan for this demo.
Do not paste the key into chat, JavaScript, a workflow, or the repository.
Set it only in Render's secret environment settings.

The configured model is `openai/gpt-oss-20b`. Check your account's Models and
Limits pages before deployment; availability and free limits can change.
Change GROQ_MODEL if necessary to a compatible chat-completions model available
to your account. There is no live web search or external tool execution here.
Requests include conversation history and are processed by Groq.

## 3. Create the Render free service

Sign in at https://dashboard.render.com and connect your GitHub account.
Choose **New → Blueprint**, select this backend repository, and use the root
`render.yaml`. Review that the web service plan is **Free** before creating it.
If the service name is unavailable, choose another name in render.yaml.

When prompted, enter:

| Setting | Value |
|---|---|
| GROQ_API_KEY | Your secret Groq API key |
| ALLOWED_ORIGINS | `https://YOUR-USERNAME.github.io` |

ALLOWED_ORIGINS is the **origin**, with no repository path: for
`https://manoj.github.io/portfolio/`, enter `https://manoj.github.io`.
For a custom portfolio domain, enter its HTTPS origin instead. Multiple origins
can be comma separated. Do not use `*`. This controls browser access; CORS is
not authentication and cannot prevent direct API calls.

The Blueprint sets AI_PROVIDER=groq, GROQ_MODEL=openai/gpt-oss-20b,
REQUESTS_PER_MINUTE=10, and MAX_CONCURRENT_REQUESTS=2.
Render builds the Dockerfile, injects its PORT, and checks `/health`.
The process runs one Uvicorn worker, as required by the in-memory demo limits.
The initial service creation deploys the app. Subsequent automatic deploys are
disabled so GitHub Actions can test before requesting deployment.

If you prefer **New → Web Service** instead of a Blueprint: select the repo,
branch `main`, language/runtime **Docker**, Dockerfile `./Dockerfile`, and
**Free** instance. Enter all six environment settings above, set health check
path `/health`, and turn Auto-Deploy **Off**. Do not create both services.

After a successful build, copy the actual service URL Render assigns, e.g.
`https://manoj-ai-assistant-xxxx.onrender.com`. Open `/health` and then `/`.
The root URL already contains a working chat page. Test one short question.
`/health` checks the process, not the validity of your Groq credentials.

## 4. Connect your existing GitHub Pages portfolio

Two options:

### Easiest: link to the complete Render chat page

Add this to your existing portfolio HTML, substituting your real Render URL:

```html
<a href="https://YOUR-SERVICE.onrender.com" target="_blank" rel="noopener">
  Chat with my AI assistant
</a>
```

No frontend copying is required. The chat interface and API share the Render origin.

### Host the chat page inside your GitHub Pages website

Copy **the contents** of `github-pages/` into a new `chat/` directory in your
existing portfolio repository. The result must be:

```text
chat/index.html
chat/static/style.css
chat/static/chat.js
chat/static/config.js
```

Edit `chat/static/config.js`:

```javascript
window.CHAT_API_BASE_URL = "https://YOUR-SERVICE.onrender.com";
```

This is a public URL, not a secret. Never add the Groq key there.
Commit and publish using your existing Pages deployment process. Add this link
to the portfolio (adjust if your portfolio uses a different directory layout):

```html
<a href="./chat/">Chat with my AI assistant</a>
```

For a project site the chat URL will be
`https://YOUR-USERNAME.github.io/YOUR-PORTFOLIO-REPO/chat/`.
Configure Render ALLOWED_ORIGINS using only `https://YOUR-USERNAME.github.io`.
The included relative asset paths work under that project subdirectory.

## 5. Enable GitHub Actions deployment

The existing `.github/workflows/tests.yml` now runs tests, JavaScript syntax
checks, and a Docker build. It requests a Render deployment only for `main`
after all checks succeed, including for a manual run on `main`.

1. In Render open your service → **Settings → Deploy Hook** and copy the secret URL.
2. In the **backend** GitHub repo open **Settings → Secrets and variables →
   Actions → New repository secret**.
3. Name: `RENDER_DEPLOY_HOOK_URL`. Value: the complete Render hook URL.
4. Push a change to `main` or use **Actions → Tests and Render deployment →
   Run workflow** on `main`.
5. Check Render's **Events/Logs** until the deployment is live.

The hook includes the tested commit SHA (`ref`), preventing a later untested
commit from being substituted. GitHub Actions checks and builds a local Docker
image; Render then builds that same commit using the Dockerfile. No GHCR or
Docker Hub account is needed. A successful hook request means **deployment
accepted**, not deployment live. Check Render for build failures. The initial
Blueprint deploy is performed before this workflow is configured.

If the secret is absent, CI still runs and prints a clear deployment-skipped
message. Pull requests never receive or use the deploy hook secret. Do not
share this hook URL; it authorizes deployment. Rotate it in Render if exposed.
Do not duplicate the workflow in a second file or enable Render auto-deploy
while using this hook approach.

## Local testing (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
$env:AI_PROVIDER = "groq"
$env:GROQ_API_KEY = "YOUR-KEY"
$env:GROQ_MODEL = "openai/gpt-oss-20b"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8081
```

Open http://127.0.0.1:8081. If entering a key into your shell, be aware your shell
may retain command history. Prefer your IDE's private environment configuration.
The app reads process environment variables; it does not automatically load `.env`.

To use the original local model instead:

```powershell
$env:AI_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "qwen3:4b"
ollama pull qwen3:4b
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8081
```

For automated tests, set AI_PROVIDER=ollama so no key or live model is needed:

```powershell
$env:AI_PROVIDER = "ollama"
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Limits and troubleshooting

- Render Free sleeps after 15 minutes without traffic; wake-up can take roughly
  a minute. Do not run artificial keep-alive jobs to bypass the free-service behavior.
- Free Render and Groq quotas apply independently. Keep paid upgrades disabled
  if you want a free-only demo. Review current account limits before launch.
- The global 10-requests/minute limit is shared by all visitors; it is not a
  per-user quota. Up to two model calls run at once. These in-memory limits reset
  on restart and do not coordinate across multiple workers or instances.
- This is a small public demo without user login or durable chat storage. It
  does not provide a complete abuse-prevention or multi-user production system.
- 429: local demo cap or Groq quota reached. Retry later; shorten questions and
  start a new chat to reduce tokens. No automatic retries consume additional quota.
- 503 authorization error: check GROQ_API_KEY in Render and save/redeploy.
- 503 model unavailable: check GROQ_MODEL against your Groq account's models.
- 502: provider error/malformed answer. Check configuration and try again.
- Chat on Render works but Pages fails: check config.js URL, HTTPS, and
  ALLOWED_ORIGINS. Use browser Network tools to inspect the preflight and POST.
- No deploy after push: confirm branch `main`, CI success, and the deploy hook
  secret in the backend repository. Inspect Render Events for the requested commit.
- To roll back on a free service, revert the problematic commit in GitHub and
  push the revert through this tested deployment flow.

## References

- https://render.com/docs/free
- https://render.com/docs/blueprint-spec
- https://render.com/docs/deploy-hooks
- https://console.groq.com/docs/models
- https://console.groq.com/docs/rate-limits
