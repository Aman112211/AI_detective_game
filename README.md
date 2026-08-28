# AI Detective

AI Detective is a work-in-progress mystery game. The current implementation contains the Flask backend API only. The React frontend, production persistence, and final game presentation are not implemented yet.

The frozen mystery is stored server-side in `backend/data/mystery-solution.json`. It is the source of truth for the case and must not be copied into frontend code or exposed by an API response.

## Current Features

- Flask REST API
- CORS support for local frontend development
- Environment variable loading with `python-dotenv`
- In-memory game sessions
- Server-authoritative question counter
- Controlled evidence discovery
- Optional LLM response adapter
- Deterministic in-character fallback when no LLM key is configured
- Server-side accusation scoring

## Setup

From the project root, create or activate a virtual environment and install the backend dependencies:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

The project has also been tested with Python 3.9.11. Flask requires a supported Python installation.

### Environment Variables

Create a `.env` file in the project root when needed:

```env
FLASK_ENV=development
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false

# Optional. If omitted, the backend uses its deterministic fallback response.
LLM_API_KEY=your-api-key
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
```

Never commit `.env` or place API keys in frontend code. The existing `.gitignore` excludes `.env`.

## Run the Backend

From the project root:

```powershell
python backend\app.py
```

The server runs at `http://127.0.0.1:5000` by default. Keep the server running in one terminal while making API requests or running the test suite.

## API Endpoints

All endpoints use the `/api` prefix.

### `GET /api/health`

Checks that the Flask application is running.

Example response:

```json
{
  "status": "ok"
}
```

### `POST /api/session`

Creates a new in-memory game session. No request body is required.

Example request:

```json
{}
```

Example response:

```json
{
  "sessionId": "generated-uuid",
  "title": "The Vanished Doubloons of the Crimson Gull",
  "briefing": "...",
  "suspects": [],
  "questionsRemaining": 15
}
```

The response contains only public case information. It does not include the answer key, suspect truth values, hidden evidence unlock conditions, or scoring data.

Sessions are lost when the Flask process restarts.

### `POST /api/chat`

Asks a question about the case. The server validates the session, checks that the game is still investigating, decrements the question counter, stores the question, discovers matching authored evidence, and returns a controlled response.

Request:

```json
{
  "sessionId": "generated-uuid",
  "message": "Where was Toby during the storm?"
}
```

Response:

```json
{
  "response": "...",
  "questionsRemaining": 14,
  "newEvidence": [],
  "discoveredEvidenceIds": [],
  "gameStatus": "investigating"
}
```

An empty message is rejected with `400`. An unknown session returns `404`. A session with no questions remaining returns `409` and does not consume another question.

The LLM receives only controlled case context. The answer key and hidden rules are never sent to it. Without `LLM_API_KEY`, the backend uses a deterministic fallback so the API can be tested without an external LLM service.

### `POST /api/submit`

Scores an accusation against the server-side answer key.

Request:

```json
{
  "sessionId": "generated-uuid",
  "culprit": "toby",
  "method": "Toby used a wire tool to pick the cabin lock during the storm and lowered the chest through the porthole to a rowboat.",
  "motive": "Captain Voss paid Toby to steal the treasure and weaken the Crimson Gull.",
  "evidence": [
    "wire_tool",
    "watch_log",
    "torn_cloth",
    "fisherman_report"
  ]
}
```

Response:

```json
{
  "score": 25,
  "breakdown": {
    "identity": 10,
    "method": 5,
    "motive": 5,
    "evidence": 5
  },
  "gameStatus": "solved"
}
```

The scoring service reads the answer key on the backend and returns only the score, neutral breakdown categories, and game status. The answer key is never returned to the browser.

## Run the API Tests

Start the backend first, then open a second terminal from the project root and run:

```powershell
python test_api.py
```

The test suite checks health, session creation, chat, evidence discovery, prompt-injection resistance, unsupported-fact resistance, invalid requests, and accusation scoring.

One test-suite expectation may need updating as the project evolves: chat requests after the question counter reaches zero are correctly rejected with `409`, as required by the server-authoritative prompt limit.

## Security Boundary

The following data remains backend-only:

- `answerKey`
- Suspect `truth` values
- Hidden evidence unlock conditions
- Internal scoring rules
- Complete mystery JSON
- LLM API credentials

Do not add `backend/data` to a public static directory, import the mystery JSON into frontend code, or store the answer key in browser storage.

## Work In Progress

Not implemented yet:

- React + Vite frontend
- Chat and accusation user interface
- Persistent sessions or database storage
- Authentication or leaderboard
- Production WSGI deployment
- Final LLM provider integration and response validation
- Animated detective character
- Audio, voice, and ambient music
- Final verdict animations
- Comprehensive automated backend test files
