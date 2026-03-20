# 🎙️ Voice-Based AI Assistant (Local API + RAG + Encryption)

## 📌 Overview

This project is a **Voice-Based AI Assistant** that integrates **Speech Recognition, Generative AI, Retrieval-Augmented Generation (RAG), and secure data handling** into a modular system.

The assistant enables users to interact using natural voice commands, execute system-level tasks, and receive intelligent responses in both text and speech formats.

Unlike conventional assistants, this system is designed with a **local API architecture**, ensuring **privacy, modularity, and scalability**.

---

## 🚀 Key Features

- 🎤 Voice Input using Microphone (Browser-based)
- 🧠 Speech-to-Text (Whisper / SpeechRecognition)
- 🔐 Encrypted Audio & Transcript Storage
- 🧭 Intent Classification (Command vs Query)
- 📚 Retrieval-Augmented Generation (RAG)
- 🤖 LLM-based Intelligent Response Generation
- ⚙️ System Automation (Open Apps, Execute Commands)
- 🔊 Text-to-Speech Output
- 🌐 React-based Interactive Frontend
- 🔗 FastAPI-based Modular Backend (Local API)

---

## 🧱 System Architecture

```
User Voice Input
      ↓
Speech-to-Text (STT)
      ↓
Intent Classification
      ↓
 ┌───────────────┐
 │               │
Command Path     Query Path
 │               │
Automation      RAG Retrieval
 │               │
 └────→ LLM Processing
          ↓
   Response Generation
          ↓
   Text-to-Speech (TTS)
          ↓
        Frontend UI
```

---

## ⚙️ Tech Stack

### Backend
- FastAPI
- Python 3.10+
- Whisper / SpeechRecognition
- LangChain
- FAISS / Vector DB
- OpenAI / HuggingFace LLMs
- pyttsx3 / gTTS

### Frontend
- React (Vite)
- HTML / CSS / JavaScript

### Security
- AES Encryption for Audio & Transcripts

---

## 🔐 Security Design

- Audio inputs are encrypted before storage  
- Transcripts are encrypted to prevent misuse  
- Processing occurs locally to reduce cloud dependency  
- Sensitive data is decrypted only in memory  

---

## 📚 RAG Pipeline

- Documents are loaded and chunked  
- Embeddings generated using sentence-transformers  
- Stored in vector database (FAISS/Chroma)  
- Similarity search retrieves relevant context  
- Context injected into LLM prompt  

---

## 📂 Project Structure

```
voice_ai_assistant/
│
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── stt_route.py
│   │   │   ├── execute_route.py
│   │   │   ├── llm_route.py
│   │   │   ├── tts_route.py
│   │   ├── main.py
│   │
│   ├── modules/
│   │   ├── stt.py
│   │   ├── rag.py
│   │   ├── llm_client.py
│   │   ├── tts.py
│   │   ├── automator.py
│   │   ├── crypto_utils.py
│
├── frontend/
│   ├── web/
│   │   ├── src/
│   │   │   ├── App.jsx
│
├── data/
│   ├── docs/
│
└── README.md
```

---

## 🔄 Working Pipeline

1. User records voice input  
2. Audio is encrypted and processed  
3. Speech is converted into text  
4. Intent is classified  
5. Command → Automation  
6. Query → RAG → LLM  
7. Response is generated  
8. Response converted to speech  
9. Output displayed on UI  

---

## ⚠️ Current Status (Phase-2)

- ✔️ Backend API structure complete  
- ✔️ Frontend integration complete  
- ✔️ Encryption implemented  
- ⚠️ STT integration in progress  
- ⚠️ RAG implementation ongoing  
- ⚠️ LLM integration in progress  

---

## 🔮 Future Scope

- Semantic intent classification using embeddings  
- Accessibility features for disabled users  
- Cross-platform deployment  
- Advanced automation workflows  
- Improved speech accuracy  

---

## 🧠 Learnings

- System design for AI pipelines  
- API-based modular architecture  
- RAG implementation  
- Voice processing systems  
- Security in AI systems  

---

## 📌 Author

**Shashwat Malviya**  
Final Year B.Tech (CSE AI & DS)

---

## ⭐ Acknowledgements

- OpenAI  
- HuggingFace  
- LangChain  
- FastAPI  
- FAISS  

---

## 📬 Contact

Feel free to connect or collaborate!
