# Hypochondriapp

A playful, satirical web app that always finds the worst possible diagnosis for your symptoms. It also includes a mini personality quiz; the worse your personality score, the harsher the dramatic diagnosis. Sometimes the result is "death" which whimsically routes you to either heaven or hell. Optionally augments the response with an Ollama Mistral LLM.

This is satire, not medical advice.

## Features
- Symptoms free-text input; keyword-based severity scoring
- Personality quiz (Likert 1–5) influences outcome severity
- Whimsical afterlife branch (heaven or hell) if the dramatic “death” occurs
- Optional LLM flair via Ollama (`mistral` model). Fallbacks gracefully if unavailable

## Quickstart

1. Create and activate venv, install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
# or
FLASK_APP=app.py flask run --host 0.0.0.0 --port 5000
```

3. Open in your browser: `http://localhost:5000`

## Optional: Enable Ollama LLM

Install Ollama and pull the `mistral` model:

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull mistral
```

The app will auto-detect Ollama at `http://localhost:11434`. You can customize via env vars:

- `DISABLE_LLM=1` to disable
- `OLLAMA_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `mistral`)

## Dev notes
- Keep tone humorous and non-graphic. This app is not medical advice.
- The deterministic logic is in `app.py`; templates in `templates/`.