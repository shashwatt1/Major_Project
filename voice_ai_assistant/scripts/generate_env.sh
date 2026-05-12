#!/usr/bin/env bash
# generate_env.sh — generates a fresh .env file with a new encryption key
# Usage:  bash scripts/generate_env.sh

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    echo "[!] .env already exists at $ENV_FILE"
    echo "    Delete it first if you want to regenerate."
    exit 0
fi

# Generate Fernet key using Python
KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

cat > "$ENV_FILE" <<EOF
# Voice AI Assistant — Environment Variables
# Generated automatically by generate_env.sh

# AES/Fernet encryption key (DO NOT SHARE OR COMMIT)
VOICE_AI_ENCRYPTION_KEY=$KEY

# Ollama local LLM settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
EOF

echo "[+] .env created at $ENV_FILE"
echo "[+] Encryption key generated successfully."
echo ""
echo "    IMPORTANT: Add .env to your .gitignore!"
