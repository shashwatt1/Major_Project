🔊 Secure Voice-Based AI Assistant (Local API + LLM + RAG)

An AI-powered, privacy-focused voice assistant designed as a modular desktop system, integrating speech recognition, generative AI reasoning, task automation, biometric authentication, and encrypted data handling.
The project emphasizes local API architecture, secure processing, and extensibility, making it suitable for real-world deployment and future accessibility use cases.

🚀 Project Overview

This project aims to build a secure and intelligent voice-based personal assistant that operates primarily on a local system while supporting cloud intelligence when required.
Unlike conventional assistants, the system is architected around a FastAPI-based local API, ensuring modularity, privacy, and controlled execution.

The assistant listens to voice commands, transcribes them accurately, classifies user intent, performs either automation or AI reasoning, and responds in a natural human-like voice.

✨ Key Features

🎙️ Speech-to-Text (STT) using Whisper / SpeechRecognition

🧠 Generative AI Reasoning using Transformer-based LLMs

🔍 Intent Classification

Current: Keyword-based (rule-based)

Future: ML/Semantic intent classification

🔐 Biometric Security with Face Authentication (LBPH algorithm)

🛡️ End-to-End Data Security

Encrypted voice recordings

Encrypted transcript storage

Secure key management

🔗 Local API Architecture (FastAPI)

Clear separation of STT, LLM, RAG, automation, and TTS modules

🔊 Text-to-Speech (TTS) for natural responses

🧩 Retrieval-Augmented Generation (RAG) using LangChain

🖥️ Desktop UI using Eel (Python + Web UI)

🧠 System Architecture (High-Level)

The system follows a modular, secure, and event-driven architecture built around a FastAPI-based local server. Each component performs a specific role and communicates through well-defined interfaces.

Processing Flow

Face Authentication (Optional)

User identity is verified using the LBPH face recognition algorithm before activating the assistant.

Voice Capture

User voice is captured through the system microphone and processed in memory.

Audio Preprocessing

Noise reduction, silence trimming, and normalization are applied to improve speech recognition accuracy.

Audio Encryption

The captured audio is encrypted using AES-based encryption before being stored, ensuring protection against misuse.

Temporary Decryption (Memory)

Encrypted audio is decrypted temporarily in memory for processing and immediately cleared afterward.

Speech-to-Text (STT)

Whisper or SpeechRecognition converts speech into text with high accuracy.

Intent Classification

The transcribed text is classified into:

Command intent (automation tasks)

Query intent (AI reasoning)

Processing Layer

Command intents are handled by the Automation module.

Query intents are processed using LLMs with Retrieval-Augmented Generation (RAG) via LangChain and a vector database.

Text-to-Speech (TTS)

The generated response is converted into natural speech using pyttsx3 or gTTS.

User Interface (UI)

The desktop UI (Eel) displays the transcript, AI response, and plays the audio output.

🔗 Local API Backbone

All system components communicate through a FastAPI-based local API, ensuring modularity and security.

Runs on localhost (127.0.0.1)

API-key protected endpoints

Clear separation of modules:

STT

Intent Classification

LLM + RAG

Automation

TTS

Authentication

🔐 Security Design

Security is treated as a first-class concern, not an afterthought.

Encrypted Audio Storage
Voice recordings are encrypted immediately after capture and never stored in plaintext.

Encrypted Transcripts
Transcriptions are encrypted before database storage, preventing leakage even if files are accessed by malware.

Memory-Safe Processing
Decryption happens only temporarily in memory during processing.

Local API Protection

API bound to localhost

API-key based access control

No external exposure by default

This design protects against misuse of stored voice samples and transcript leakage.

🧠 Intent Classification
Current Approach

Keyword-based intent classification

Distinguishes between:

Actionable commands (open apps, automate tasks)

Informational queries (sent to LLM)

Future Scope

Semantic / ML-based intent classification

Embedding-based or Transformer-based models

Better handling of complex phrasing and accessibility scenarios

📚 Retrieval-Augmented Generation (RAG)

To strengthen AI reasoning and reduce hallucinations, the assistant supports RAG using LangChain.

How it works:

User query is converted to embeddings

Relevant documents are retrieved from a local vector store

Retrieved context is injected into the LLM prompt

LLM generates a grounded, context-aware response

Use cases:

Project documentation Q&A

Domain-specific knowledge

Accessibility workflows

Offline knowledge support

🛠️ Tech Stack

Programming Language: Python

Backend / API: FastAPI

STT: OpenAI Whisper, SpeechRecognition

LLM: OpenAI API / HuggingFace Transformers

RAG: LangChain, FAISS / ChromaDB

TTS: pyttsx3 / gTTS

Face Recognition: OpenCV (LBPH)

UI: Eel (HTML + JS + Python)

Security: AES-based encryption, OS key management

Database: SQLite / SQLCipher (planned)

⚙️ Hardware Requirements

macOS / Windows / Linux

No dedicated GPU required

Works efficiently on Apple Silicon (M1/M2/M3/M4)

Microphone & Webcam (for voice & face authentication)

♿ Accessibility & Social Impact (Future Scope)

Voice-only interaction for visually impaired users

High-accuracy transcription with confirmation layers

Voice-driven UPI payments and navigation assistance

Cross-platform support (mobile & edge devices)

📈 Why This Project Matters

Demonstrates real-world AI system design

Combines ML, GenAI, Security, APIs, and Automation

Emphasizes privacy-first local processing

Scalable and extensible architecture

Strong alignment with industry AI practices

📌 Status

🟢 Active development (Final Year Major Project)
🔜 Planned enhancements: Semantic intent classification, advanced RAG, accessibility-focused workflows

👤 Author

Shashwat Malviya
Final Year Engineering Student | AI / ML Enthusiast
📌 Interests: Generative AI, System Design, Secure AI, Accessibility Tech
