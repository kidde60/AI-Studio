# AI Studio Backend

The backend is a FastAPI service for user accounts, AI-assisted video content,
storyboards, media selection, and video production. It uses PostgreSQL for
application data and stores uploaded/generated media in `backend/app/storage/`.

## Requirements

- Python 3.10 or newer
- PostgreSQL database reachable from this machine
- Ollama for local content and storyboard generation
- FFmpeg with the `ass` subtitle filter for video rendering (on macOS with
  Homebrew, the backend's renderer recommends `brew install ffmpeg-full`)

Gemini, Pexels, and Pixabay API keys are only needed for the optional features
that use those providers. The backend currently has no checked-in Python
dependency manifest, so the install command below lists its direct dependencies.

## Set up and start

Run these commands from the repository root:

```bash
cd backend/app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "uvicorn[standard]" fastapi sqlalchemy asyncpg pydantic-settings python-dotenv httpx "python-jose[cryptography]" "passlib[bcrypt]" python-multipart email-validator google-genai openai
```

Create a private `backend/app/.env` file. The settings loader reads `.env` from
the current working directory, so start Uvicorn from `backend/app` as shown
below.

```dotenv
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE
JWT_SECRET_KEY=replace-with-a-long-random-secret

# Ollama is the default AI provider.
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Optional integrations:
# GEMINI_API_KEY=
# PEXELS_API_KEY=
# PIXABAY_API_KEY=
# OPENAI_API_KEY=
```

`DATABASE_URL` is required. Use a PostgreSQL database and keep real credentials
in the ignored `.env` file; do not commit them.

Install Ollama (for example, `brew install ollama` on macOS), then prepare the
model and start Ollama in a separate terminal. If Ollama is already running as
a background service, skip `ollama serve`.

```bash
ollama pull qwen2.5:7b
ollama serve
```

Then, in another terminal, start the API from `backend/app`:

```bash
cd backend/app
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check that the API is running:

```bash
curl http://127.0.0.1:8000/health
```

The health endpoint returns `{"status":"ok","service":"ai-video-studio-api"}`.
Interactive API documentation is available at
<http://127.0.0.1:8000/docs>; OpenAPI JSON is at
<http://127.0.0.1:8000/openapi.json>.

## How the local LLM works

Ollama runs the model locally as a separate service; the backend does not load
model weights itself. By default, the backend sends requests to
`http://localhost:11434` using Ollama's `/api/chat` endpoint and the
`qwen2.5:7b` model. It asks Ollama for JSON responses, validates the expected
content/storyboard fields, and then saves successful results in PostgreSQL.
Generation requests can take several minutes, so the Ollama HTTP client uses a
long timeout.

To use a different local model or Ollama host, change `OLLAMA_MODEL` and/or
`OLLAMA_BASE_URL` in `backend/app/.env`. The model must already be available to
Ollama; for example, download it with `ollama pull <model-name>`.

`AI_PROVIDER` selects the content and storyboard provider:

| `AI_PROVIDER` | Content generation | Storyboard generation |
| --- | --- | --- |
| `ollama` (default) | Local Ollama model | Local Ollama model |
| `gemini` | Gemini API | Gemini API |
| `openai` | OpenAI API | Mock provider |
| `mock` | Mock provider | Mock provider |

The mock providers are useful for exercising the API without an LLM. Speech
synthesis is separate from `AI_PROVIDER`: text-to-speech currently always uses
Gemini and requires `GEMINI_API_KEY`. Stock media search uses Pexels and/or
Pixabay when their corresponding API keys are configured.

## Request and production flow

1. A user registers or logs in. The API returns a JWT access token, which is
   required by protected endpoints.
2. The user creates a project and asks the content endpoint to generate a
   script. The selected AI provider generates it; the backend validates and
   persists the result.
3. The user generates a storyboard from saved content. The provider returns
   scenes with narration and visual descriptions, which the backend saves.
4. Scene media can be searched from configured stock providers or selected
   from uploaded assets. The automatic production endpoint can choose media
   for scenes.
5. Narration can be edited, converted to subtitles, and synthesized to audio.
   Audio and uploaded media files are stored locally under `storage/`.
6. A render request starts a background task in the API process. FFmpeg combines
   scene media, narration/audio, subtitles, and optional project music into an
   MP4. The client polls the render-job endpoint and downloads the completed
   video.

Render jobs use FastAPI's in-process background tasks, not a separate durable
queue. A process restart can interrupt a render in progress.

## API areas

All versioned endpoints are under `/api/v1`:

- `/auth` — registration, login, and current-user lookup
- `/projects` — project CRUD
- `/content` — AI content generation, edits, and content versions
- `/storyboards` — storyboard and scene creation, generation, and media selection
- `/media` — stock media search
- `/assets` — upload, list, download, and delete user media
- `/production-assets` — automatic scene assets, scene editing, and readiness
- `/tts` — scene voice generation and audio retrieval
- `/production` — subtitles, project music, render jobs, and rendered video

Most endpoints require `Authorization: Bearer <access-token>`. The frontend
uses `http://localhost:8000/api/v1` by default.

## Backend structure

- `app/main.py` — FastAPI app, health endpoint, CORS, and startup/shutdown hooks
- `app/api/v1/` — HTTP route handlers grouped by feature
- `app/schemas/` — Pydantic request and response models
- `app/models/` — SQLAlchemy database models
- `app/db/session.py` — async PostgreSQL engine and request-scoped sessions
- `app/services/` — business logic for auth, content, projects, media, and
  production
- `app/services/ai/` — provider interfaces, provider selection, and AI clients
- `app/core/` — environment configuration and JWT/security utilities
- `app/storage/` — local uploaded assets, generated audio, music, and renders

At startup, the app creates registered database tables if they do not exist.
This is a development/MVP convenience, not a migration system; schema changes
for production should use migrations. The current CORS middleware permits all
origins, so restrict it before exposing the API outside a trusted local
development environment.
