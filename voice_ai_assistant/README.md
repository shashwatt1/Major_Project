# Voice AI Assistant

A local-first Voice AI Assistant built with FastAPI and a lightweight frontend. The system accepts voice commands, converts speech to text, routes the text through an LLM (with RAG-ready hooks), and returns spoken responses. It also supports local command execution such as opening apps on macOS (e.g., “open apple music”). Audio inputs and transcripts are stored encrypted at rest.

---

## Table of Contents

1. Project Overview
2. Goals and Scope
3. System Architecture
4. End-to-End Flow
5. Features
6. Security and Encryption
7. API Reference
8. Frontend
9. Backend Modules
10. RAG Integration (Planned)
11. Local Command Execution
12. Data and Storage
13. Configuration
14. Installation
15. Running the Project
16. Testing
17. Troubleshooting
18. Roadmap
19. Contributing
20. License

---

## 1. Project Overview

Voice AI Assistant is a local REST API + web UI that enables voice-based interaction with an LLM. The focus is on local control, data privacy, and extensibility. The system captures audio, transcribes it, optionally enriches it with retrieval-augmented generation (RAG), sends the prompt to a language model, and returns a spoken response. It also includes a simple automation layer to execute local tasks such as launching desktop apps.

This repository is structured to keep the API modular and allow you to incrementally improve the pipeline—swap in a new STT engine, add a vector database, or connect a different LLM provider without rewriting the entire app.

---

## 2. Goals and Scope

### Primary Goals

- Provide a local voice-based interface for user commands.
- Keep captured audio and text encrypted at rest.
- Support a standard REST API for easy integration.
- Enable local command execution (macOS apps).
- Offer a minimal but clear UI for recording and testing the pipeline.

### Non-Goals (for now)

- Cloud deployment
- User authentication across devices
- Multi-tenant or enterprise-level permissioning

---

## 3. System Architecture

At a high level, the system is split into three layers:

1. **Frontend (Web UI)**
   - Built with React + Vite
   - Records audio via the browser
   - Sends audio to the backend
   - Displays transcript and LLM response
   - Plays back TTS audio

2. **Backend API (FastAPI)**
   - Handles STT, LLM, and TTS endpoints
   - Encrypts audio and transcripts at rest
   - Exposes a command execution endpoint

3. **Modules**
   - STT: placeholder for Whisper/SpeechRecognition
   - LLM Client: placeholder for OpenAI/HF models
   - TTS: pyttsx3 fallback (silent wav if backend not available)
   - Automator: app launch on macOS

---

## 4. End-to-End Flow

The end-to-end pipeline works as follows:

1. User records or uploads audio in the UI.
2. `/stt/transcribe` receives the file.
3. Audio is encrypted and stored.
4. Audio is decrypted temporarily and sent to STT.
5. Transcript is encrypted and stored.
6. `/llm/generate` uses transcript text to generate response.
7. `/tts/speak` converts text response to audio.
8. Frontend plays back the TTS audio.

For local automation, `/execute/run` accepts commands such as:

- `open apple music`
- `open whatsapp`
- `open https://youtube.com`

---

## 5. Features

- **Speech-to-Text (STT)**: Integrates with Whisper or SpeechRecognition.
- **Text-to-Speech (TTS)**: Generates audio responses (pyttsx3 fallback).
- **LLM Integration**: Placeholder module for OpenAI or Hugging Face.
- **RAG-Ready**: Modular design for future retrieval enhancements.
- **Local Command Execution**: Open apps and URLs on macOS.
- **Encrypted Storage**: Audio and transcripts are encrypted at rest.

---

## 6. Security and Encryption

The system uses symmetric encryption (Fernet) to protect user audio and transcripts on disk. The encryption key is provided via environment variable:

```
VOICE_AI_ENCRYPTION_KEY
```

**Key management guidelines:**

- Generate once and store securely (do not commit to git).
- Rotate keys carefully if you plan to maintain data compatibility.
- Keep different keys for development and production.

Encrypted files are stored under:

- `voice_ai_assistant/data/encrypted_audio`
- `voice_ai_assistant/data/encrypted_transcripts`

---

## 7. API Reference

### Health

`GET /health`

Response:

```
{ "status": "ok" }
```

---

### STT

`POST /stt/transcribe`

**Request:**

- `multipart/form-data` with `file`

**Response:**

```
{
  "text": "transcribed text",
  "audio_id": "...",
  "transcript_id": "..."
}
```

---

### LLM

`POST /llm/generate`

**Request:**

```
{
  "prompt": "your text here"
}
```

**Response:**

```
{
  "response": "llm response"
}
```

---

### TTS

`POST /tts/speak`

**Request:**

```
{
  "text": "reply to speak"
}
```

**Response:**

```
{
  "audio_base64": "...",
  "audio_path": "..."
}
```

---

### Execute

`POST /execute/run`

**Request:**

```
{
  "command": "open apple music"
}
```

**Response:**

```
{
  "status": "ok",
  "info": "Opened app: Music"
}
```

---

## 8. Frontend

The frontend lives at:

```
voice_ai_assistant/frontend/web
```

It provides:

- Record/Stop buttons using MediaRecorder
- Upload fallback
- Transcript display
- LLM response display
- Audio playback for TTS

The UI is minimal but visually clean with a modern typography pairing and soft background gradients.

---

## 9. Backend Modules

### `modules/stt.py`

- Placeholder for speech-to-text implementation.
- Replace with Whisper or your preferred STT engine.

### `modules/llm_client.py`

- Placeholder for LLM integration.
- Supports OpenAI or HF models.

### `modules/tts.py`

- Basic TTS implementation using `pyttsx3` if available.
- Falls back to silent WAV.

### `modules/automator.py`

- Executes local commands.
- Currently supports `open` on macOS.

### `modules/crypto_utils.py`

- Encryption helpers for data at rest.

---

## 10. RAG Integration (Planned)

RAG (Retrieval-Augmented Generation) is a core planned improvement. The idea is to fetch relevant knowledge chunks from a local or hosted vector database and inject them into the prompt before sending it to the LLM.

Suggested steps:

1. Ingest documents → chunk → embed → store vectors.
2. On request, embed query and retrieve top-k matches.
3. Create a prompt template: system + retrieved context + user query.
4. Feed to LLM.

Recommended tools:

- `sentence-transformers` or OpenAI embeddings
- `FAISS` or `Chroma`

---

## 11. Local Command Execution

The command execution layer supports simple natural language commands.

Examples:

- `open apple music`
- `open whatsapp`
- `open https://youtube.com`

Add more aliases in:

```
backend/modules/automator.py
```

This is intentionally simple. In production, you would add:

- Command classification
- Intent detection
- Safety checks and allowlists

---

## 12. Data and Storage

By default, data is stored in:

```
voice_ai_assistant/data
```

Subfolders include:

- `encrypted_audio`
- `encrypted_transcripts`
- `tts_audio`

Only encrypted data should be persisted. Temporary decrypted files are kept only in memory or in a temporary file that is discarded after use.

---

## 13. Configuration

Environment variables used:

- `VOICE_AI_ENCRYPTION_KEY`: Required for encryption at rest.
- `VITE_API_BASE`: Optional frontend override for API base URL.

---

## 14. Installation

### Backend

```
cd voice_ai_assistant/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```
cd voice_ai_assistant/frontend/web
npm install
```

---

## 15. Running the Project

### Backend

```
cd voice_ai_assistant/backend
export VOICE_AI_ENCRYPTION_KEY="your_key_here"
uvicorn api.main:app --reload --port 8000
```

### Frontend

```
cd voice_ai_assistant/frontend/web
npm run dev
```

Open `http://localhost:5173`.

---

## 16. Testing

Tests folder structure is created but no tests exist yet. Suggested first tests:

- STT upload returns transcript
- Encryption key missing returns error
- LLM route responds
- TTS returns valid base64
- Execute route returns ok for known apps

---

## 17. Troubleshooting

### Common Issues

- **CORS errors**: Ensure backend is running and CORS includes `localhost:5173`.
- **No microphone access**: Check browser permissions.
- **Encryption errors**: Ensure `VOICE_AI_ENCRYPTION_KEY` is set.
- **TTS returns silence**: pyttsx3 may not be installed or configured.

---

## 18. Roadmap

Short-term:

- Real STT (Whisper) integration
- Real TTS voice selection
- Add `/pipeline/run` endpoint
- Simple RAG retrieval layer

Medium-term:

- Intent classification for commands
- App control actions (pause, play, volume)
- Per-user encryption key vault

Long-term:

- Local desktop app wrapper
- Offline LLM and embeddings
- Cross-device sync (optional)

---

## 19. Contributing

Contributions are welcome. Please follow best practices:

- Keep modules small and testable
- Add tests for new behaviors
- Document all new endpoints

---

## 20. License

TBD. Add a license file when ready.

