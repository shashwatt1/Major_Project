#!/usr/bin/env bash
# run_local_api.sh — starts the Voice AI Assistant backend
# Usage:  bash scripts/run_local_api.sh

set -e

# Resolve project root (directory containing this script's parent)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "============================================"
echo "  Voice AI Assistant — Backend Startup"
echo "============================================"
echo "Project root: $PROJECT_ROOT"

# ── 1. Load .env if it exists ──────────────────────────────────────────────
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    echo "[+] Loading environment from .env"
    set -o allexport
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +o allexport
else
    echo "[!] WARNING: .env file not found at $PROJECT_ROOT/.env"
    echo "    Run: bash scripts/generate_env.sh"
fi

# ── 2. Activate venv ────────────────────────────────────────────────────────
VENV_DIR="$PROJECT_ROOT/venv"
if [ -d "$VENV_DIR" ]; then
    echo "[+] Activating venv: $VENV_DIR"
    source "$VENV_DIR/bin/activate"
else
    echo "[!] ERROR: venv not found at $VENV_DIR"
    echo "    Run:  python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

# ── 3. Check Ollama is running ───────────────────────────────────────────────
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[!] WARNING: Ollama does not appear to be running."
    echo "    Start it with:  ollama serve"
    echo "    The backend will still start but LLM calls will fail."
fi

# ── 4. Ensure data directories exist ────────────────────────────────────────
mkdir -p "$PROJECT_ROOT/data/encrypted_audio"
mkdir -p "$PROJECT_ROOT/data/encrypted_transcripts"
mkdir -p "$PROJECT_ROOT/data/tts_audio"
mkdir -p "$PROJECT_ROOT/data/docs"

# ── 5. Start FastAPI ─────────────────────────────────────────────────────────
echo ""
echo "[+] Starting FastAPI on http://localhost:8000"
echo "[+] API docs: http://localhost:8000/docs"
echo ""

cd "$PROJECT_ROOT"
PYTHONPATH="$PROJECT_ROOT/backend" \
    uvicorn api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
