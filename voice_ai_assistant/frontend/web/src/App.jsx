import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function base64ToBlob(base64, mimeType = "audio/wav") {
  const byteChars = atob(base64);
  const byteNumbers = new Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i += 1) {
    byteNumbers[i] = byteChars.charCodeAt(i);
  }
  return new Blob([new Uint8Array(byteNumbers)], { type: mimeType });
}

export default function App() {
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [assistantResponse, setAssistantResponse] = useState("");
  const [ttsUrl, setTtsUrl] = useState("");
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");
  const [intent, setIntent] = useState("");

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);
  const audioPlayerRef = useRef(null);

  const stopTts = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
    }
  };

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      if (ttsUrl) URL.revokeObjectURL(ttsUrl);
    };
  }, [audioUrl, ttsUrl]);

  const resetOutputs = () => {
    setTranscript("");
    setAssistantResponse("");
    setTtsUrl("");
    setIntent("");
  };

  const startRecording = async () => {
    setError("");
    resetOutputs();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        setAudioBlob(blob);
        if (audioUrl) URL.revokeObjectURL(audioUrl);
        setAudioUrl(URL.createObjectURL(blob));
        setStatus("Recording saved");
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
      setStatus("Recording...");
    } catch (err) {
      setError("Microphone permission denied or unavailable.");
      setStatus("Idle");
    }
  };

  const stopRecording = () => {
    if (!mediaRecorderRef.current) return;
    mediaRecorderRef.current.stop();
    setRecording(false);
    setStatus("Processing audio...");

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    resetOutputs();
    setAudioBlob(file);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(URL.createObjectURL(file));
    setStatus("File ready");
  };

  const runAssistant = async () => {
    if (!audioBlob) {
      setError("Please record or upload audio first.");
      return null;
    }

    setStatus("Running assistant pipeline...");
    setError("");

    const fileName = audioBlob.name || "recording.webm";
    const file = audioBlob instanceof File ? audioBlob : new File([audioBlob], fileName, { type: audioBlob.type });

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/assistant/run`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let message = "Assistant request failed.";
      try {
        const errorData = await response.json();
        message = errorData.detail || message;
      } catch {
        message = await response.text() || message;
      }
      throw new Error(message);
    }

    const data = await response.json();
    setTranscript(data.transcript || "");
    setAssistantResponse(data.response || "");
    setIntent(data.intent || "");

    let finalAudioUrl = "";
    if (data.audio_base64) {
      if (ttsUrl) URL.revokeObjectURL(ttsUrl);
      const blob = base64ToBlob(data.audio_base64);
      finalAudioUrl = URL.createObjectURL(blob);
      setTtsUrl(finalAudioUrl);
    } else if (data.response) {
      // Fallback: call POST /tts/speak automatically using the generated response text
      setStatus("Generating audio...");
      try {
        const ttsResp = await fetch(`${API_BASE}/tts/speak`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: data.response })
        });
        if (ttsResp.ok) {
          const ttsData = await ttsResp.json();
          if (ttsData.audio_base64) {
            if (ttsUrl) URL.revokeObjectURL(ttsUrl);
            const blob = base64ToBlob(ttsData.audio_base64);
            finalAudioUrl = URL.createObjectURL(blob);
            setTtsUrl(finalAudioUrl);
          }
        }
      } catch (err) {
        console.error("TTS fetch failed:", err);
      }
    }

    // Autoplay is handled natively by the <audio autoPlay> DOM element,
    // which ensures the user can use the visible controls to stop it.

    setStatus("Done");
    return data;
  };

  const runSttOnly = async () => {
    try {
      resetOutputs();
      if (!audioBlob) {
        setError("Please record or upload audio first.");
        return;
      }

      setStatus("Uploading for transcription...");
      setError("");

      const fileName = audioBlob.name || "recording.webm";
      const file = audioBlob instanceof File ? audioBlob : new File([audioBlob], fileName, { type: audioBlob.type });
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE}/stt/transcribe`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let message = "STT request failed.";
        try {
          const errorData = await response.json();
          message = errorData.detail || message;
        } catch {
          message = await response.text() || message;
        }
        throw new Error(message);
      }

      const data = await response.json();
      setTranscript(data.text || "");
      setStatus("Transcript ready");
    } catch (err) {
      setError(err.message || "STT failed.");
      setStatus("Idle");
    }
  };

  const runFullPipeline = async () => {
    try {
      resetOutputs();
      await runAssistant();
    } catch (err) {
      setError(err.message || "Pipeline failed.");
      setStatus("Idle");
    }
  };

  const clearAll = () => {
    stopTts();
    setAudioBlob(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    if (ttsUrl) URL.revokeObjectURL(ttsUrl);
    setAudioUrl("");
    setTtsUrl("");
    setTranscript("");
    setAssistantResponse("");
    setIntent("");
    setStatus("Idle");
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Local Voice AI Assistant</p>
          <h1>Speak, Understand, Respond</h1>
          <p className="subhead">
            Record audio once and let the backend handle STT, intent routing, command execution,
            RAG, LLM generation, and spoken output with encrypted storage.
          </p>
        </div>
        <div className="status-card">
          <p className="label">Status</p>
          <p className="status">{status}</p>
          {intent ? <p className="label">Intent: {intent}</p> : null}
          {error ? <p className="error">{error}</p> : null}
        </div>
      </header>

      <section className="panel">
        <h2>Input</h2>
        <div className="controls">
          <button className="primary" onClick={startRecording} disabled={recording}>
            Start Recording
          </button>
          <button className="ghost" onClick={stopRecording} disabled={!recording}>
            Stop
          </button>
          <label className="file">
            <input ref={fileInputRef} type="file" accept="audio/*" onChange={handleFileChange} />
            Upload Audio
          </label>
          <button className="ghost" onClick={clearAll}>
            Clear
          </button>
        </div>

        {audioUrl ? (
          <div className="audio-preview">
            <p className="label">Preview</p>
            <audio controls src={audioUrl} />
          </div>
        ) : (
          <p className="hint">Record or upload audio to get started.</p>
        )}
      </section>

      <section className="panel grid">
        <div>
          <h2>Speech to Text</h2>
          <p className="hint">Encrypted audio is stored after transcription.</p>
          <button className="primary" onClick={runSttOnly}>
            Run STT
          </button>
          <textarea value={transcript} readOnly placeholder="Transcript will appear here..." />
        </div>
        <div>
          <h2>LLM Response</h2>
          <p className="hint">Queries use RAG, commands execute locally, and both return speech.</p>
          <button className="primary" onClick={runFullPipeline}>
            Run Full Pipeline
          </button>
          <textarea value={assistantResponse} readOnly placeholder="Assistant response will appear here..." />
        </div>
      </section>

      <section className="panel">
        <h2>Text to Speech</h2>
        <p className="hint">Encrypted transcript stored; audio response rendered below.</p>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {ttsUrl ? <audio ref={audioPlayerRef} controls autoPlay src={ttsUrl} /> : <p className="hint">No audio yet.</p>}
          {ttsUrl && (
            <button className="ghost" onClick={stopTts}>
              Stop Audio
            </button>
          )}
        </div>
      </section>

      <footer className="footer">
        <p>API base: {API_BASE}</p>
      </footer>
    </div>
  );
}
