# AI Detective

AI Detective is a full-stack mystery game with a Flask API backend and a React + Vite frontend.

## What’s implemented

- Flask REST API (`/api/health`, `/api/session`, `/api/chat`, `/api/submit`)
- React single-page game UI (case selection, briefing, interrogation log, evidence board, accusation modal, scoring screen)
- Two playable case modes: `pirate` and `noir`
- In-memory server-side sessions with question limits and evidence discovery
- Server-side accusation scoring
- Optional LLM adapter with deterministic fallback when `LLM_API_KEY` is not set

## Project structure

- `/backend` — Flask API, routes, and game logic
- `/backend/data` — server-side mystery files (source of truth)
- `/frontend` — React + Vite client
- `/test_api.py` — API smoke/integration test script

## Prerequisites

- Python 3.9+
- Node.js 18+
- npm

## Backend setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Backend environment variables

Create a `.env` in the repository root (optional defaults shown):

```env
FLASK_ENV=development
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false

# Optional LLM config
LLM_API_KEY=
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
```

Run the backend:

```bash
python backend/app.py
```

## Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Optional frontend env (`frontend/.env`):

```env
VITE_API_URL=http://127.0.0.1:5000
```

Vite dev server typically runs at `http://127.0.0.1:5173`.

## API overview

All endpoints are prefixed with `/api`.

### `GET /api/health`
Returns:

```json
{ "status": "ok" }
```

### `POST /api/session`
Creates a new session.

Request body (optional):

```json
{ "mode": "pirate" }
```

Supported modes: `pirate`, `noir` (invalid values fall back to `pirate`).

Response includes:

- `sessionId`
- `mode`
- `title`
- `briefing`
- `setting`
- `detectiveCharacter`
- `suspects`
- `questionsRemaining`

### `POST /api/chat`
Asks a question in an active session.

Request:

```json
{
  "sessionId": "generated-uuid",
  "message": "Where was Toby during the storm?"
}
```

Response includes:

- `response`
- `questionsRemaining`
- `newEvidence`
- `discoveredEvidenceIds`
- `gameStatus`

Validation behavior:

- Missing/invalid `sessionId` or empty `message` → `400`
- Unknown session → `404`
- Finished session or no questions remaining → `409`

### `POST /api/submit`
Submits a final accusation.

Request:

```json
{
  "sessionId": "generated-uuid",
  "culprit": "toby",
  "method": "...",
  "motive": "...",
  "evidence": ["wire_tool", "watch_log"]
}
```

Response:

```json
{
  "score": 20,
  "breakdown": {
    "identity": 10,
    "method": 5,
    "motive": 5,
    "evidence": 0
  },
  "gameStatus": "investigating"
}
```

A perfect score sets `gameStatus` to `solved`.

## Running tests

Start the backend first, then from repo root:

```bash
python test_api.py
```

## Security boundary

The following remain backend-only and must not be exposed to frontend code:

- `answerKey`
- hidden evidence unlock rules
- internal scoring rules
- complete mystery JSON internals
- LLM credentials

Do not commit `.env` files or API keys.
