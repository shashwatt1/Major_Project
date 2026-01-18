# Secure Voice-Based AI Assistant  
*(Local API · LLM · RAG · Encryption · Automation)*

An AI-powered, privacy-first voice assistant built as a **modular desktop system**, integrating **speech recognition, generative AI reasoning, retrieval-augmented generation (RAG), biometric authentication, automation, and encrypted data handling**.

This project is developed as a **Final Year Major Project**, with strong emphasis on **real-world system architecture, security, and AI engineering best practices**.

---

## 📌 Project Overview

The Secure Voice-Based AI Assistant enables users to interact with their system using natural voice commands.  
It listens to user speech, transcribes it accurately, understands intent, performs intelligent reasoning or task automation, and responds in a natural human-like voice.

Unlike conventional assistants, this system is built around a **FastAPI-based local API**, ensuring modularity, privacy, and controlled execution of AI components.

---

## ✨ Key Features

- Voice-driven natural interaction  
- Speech-to-Text (STT) using Whisper / SpeechRecognition  
- Generative AI reasoning using Transformer-based LLMs  
- Retrieval-Augmented Generation (RAG) using LangChain  
- Keyword-based intent classification (current)  
- Face authentication using LBPH (optional)  
- End-to-end encryption for audio and transcripts  
- Local API architecture using FastAPI  
- Desktop UI using Eel (Python + Web UI)  
- Privacy-first local processing with hybrid cloud support  

---

## 🧠 System Architecture (High-Level)

The system follows a modular and event-driven architecture, where each component performs a specific role and communicates through a local API.

### Processing Flow

- Face Authentication (Optional)  
  User identity is verified using the LBPH face recognition algorithm before activating the assistant.

- Voice Capture  
  Voice input is captured via the system microphone and processed in memory.

- Audio Preprocessing  
  Noise reduction, silence trimming, and normalization are applied to improve transcription accuracy.

- Audio Encryption  
  Recorded audio is encrypted using AES-based encryption before storage.

- Temporary Decryption (Memory)  
  Encrypted audio is decrypted only in memory for processing and immediately cleared.

- Speech-to-Text (STT)  
  Whisper or SpeechRecognition converts speech into text.

- Intent Classification  
  Transcribed text is classified into:
  - Command intent (automation)
  - Query intent (AI reasoning)

- Processing Layer  
  - Commands are handled by the Automation module  
  - Queries are processed using LLMs with RAG (LangChain + Vector DB)

- Text-to-Speech (TTS)  
  AI responses are converted into speech using pyttsx3 or gTTS.

- User Interface (UI)  
  Desktop UI displays transcripts, responses, and plays audio output.

---

## 🔗 Local API Architecture

The **local API is the backbone of the system**.

- Built using FastAPI  
- Runs on `127.0.0.1`  
- API-key protected endpoints  
- Enables clean separation of concerns  

### Major API Modules

- `/stt` – Speech-to-text processing  
- `/intent` – Intent classification  
- `/rag_query` – RAG-based LLM reasoning  
- `/execute` – Automation commands  
- `/tts` – Text-to-speech  
- `/auth` – Face authentication  

---

## 🔐 Security Design

Security is treated as a first-class concern.

- Encrypted audio recordings (AES-based)  
- Encrypted transcript storage  
- Temporary in-memory decryption only  
- No plaintext storage of sensitive data  
- Localhost-only API access  
- API-key validation for requests  

---

## 🧠 Intent Classification

### Current Implementation
- Rule-based / keyword-based intent classification  
- Fast and reliable for common commands  

### Future Scope
- Semantic intent classification using ML models  
- Embedding-based or Transformer-based classifiers  
- Improved understanding for accessibility and complex queries  

---

## 📚 Retrieval-Augmented Generation (RAG)

To enhance accuracy and reduce hallucinations, the assistant uses RAG.

### RAG Workflow

1. User query is converted into embeddings  
2. Relevant documents are retrieved from a vector database  
3. Retrieved context is injected into the LLM prompt  
4. LLM generates grounded, context-aware responses  

### Use Cases

- Project documentation Q&A  
- Domain-specific knowledge  
- Offline knowledge retrieval  
- Accessibility-focused workflows  

---

## 🛠️ Technology Stack

- Language: Python  
- Backend: FastAPI  
- STT: Whisper, SpeechRecognition  
- LLM: OpenAI API / HuggingFace Transformers  
- RAG: LangChain, FAISS / ChromaDB  
- TTS: pyttsx3, gTTS  
- Face Recognition: OpenCV (LBPH)  
- UI: Eel  
- Database: SQLite / SQLCipher (planned)  
- Security: AES encryption, OS key management  

---

## ⚙️ Hardware Requirements

- macOS / Windows / Linux  
- No dedicated GPU required  
- Optimized for Apple Silicon (M1/M2/M3/M4)  
- Microphone and webcam  

---

## ♿ Accessibility & Future Scope

- Voice-only interaction for visually impaired users  
- High-accuracy transcription with confirmation layers  
- Voice-driven UPI payments  
- Cross-platform (mobile + desktop) support  
- Assistive automation for daily tasks  

---

## 📈 Why This Project Stands Out

- Real-world AI system architecture  
- Secure local-first design  
- Modular API-based engineering  
- Integration of LLMs + RAG  
- Strong focus on privacy and accessibility  

---

## 📌 Project Status

- Active Development (Final Year Major Project)  
- Phase-1 completed  
- Security and RAG integration in progress  

---

## 👤 Author

**Shashwat Malviya**  
Final Year Engineering Student  
Interests: Generative AI, System Design, Secure AI, Accessibility Tech  
