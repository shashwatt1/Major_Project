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
  const [llmResponse, setLlmResponse] = useState("");
  const [ttsUrl, setTtsUrl] = useState("");
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      if (ttsUrl) URL.revokeObjectURL(ttsUrl);
    };
  }, [audioUrl, ttsUrl]);

  const resetOutputs = () => {
    setTranscript("");
    setLlmResponse("");
    setTtsUrl("");
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

  const uploadToStt = async () => {
    if (!audioBlob) {
      setError("Please record or upload audio first.");
      return null;
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
      const message = await response.text();
      throw new Error(message || "STT request failed.");
    }

    const data = await response.json();
    setTranscript(data.text || "");
    setStatus("Transcription complete");
    return data;
  };

  const runSttOnly = async () => {
    try {
      resetOutputs();
      await uploadToStt();
    } catch (err) {
      setError(err.message || "STT failed.");
      setStatus("Idle");
    }
  };

  const runFullPipeline = async () => {
    try {
      resetOutputs();
      const sttData = await uploadToStt();
      if (!sttData?.text) return;

      setStatus("Generating LLM response...");
      const llmRes = await fetch(`${API_BASE}/llm/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: sttData.text }),
      });

      if (!llmRes.ok) {
        const message = await llmRes.text();
        throw new Error(message || "LLM request failed.");
      }

      const llmData = await llmRes.json();
      setLlmResponse(llmData.response || "");

      if (!llmData.response) {
        setStatus("LLM response empty");
        return;
      }

      setStatus("Generating speech...");
      const ttsRes = await fetch(`${API_BASE}/tts/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: llmData.response }),
      });

      if (!ttsRes.ok) {
        const message = await ttsRes.text();
        throw new Error(message || "TTS request failed.");
      }

      const ttsData = await ttsRes.json();
      if (ttsData.audio_base64) {
        if (ttsUrl) URL.revokeObjectURL(ttsUrl);
        const blob = base64ToBlob(ttsData.audio_base64);
        setTtsUrl(URL.createObjectURL(blob));
      }

      setStatus("Done");
    } catch (err) {
      setError(err.message || "Pipeline failed.");
      setStatus("Idle");
    }
  };

  const clearAll = () => {
    setAudioBlob(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    if (ttsUrl) URL.revokeObjectURL(ttsUrl);
    setAudioUrl("");
    setTtsUrl("");
    setTranscript("");
    setLlmResponse("");
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
            Record audio, run speech-to-text, get an LLM response with RAG-ready hooks,
            and hear the reply. Everything runs locally with encrypted storage.
          </p>
        </div>
        <div className="status-card">
          <p className="label">Status</p>
          <p className="status">{status}</p>
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
          <p className="hint">RAG can be added in the backend retrieval step.</p>
          <button className="primary" onClick={runFullPipeline}>
            Run Full Pipeline
          </button>
          <textarea value={llmResponse} readOnly placeholder="LLM response will appear here..." />
        </div>
      </section>

      <section className="panel">
        <h2>Text to Speech</h2>
        <p className="hint">Encrypted transcript stored; audio response rendered below.</p>
        {ttsUrl ? <audio controls src={ttsUrl} /> : <p className="hint">No audio yet.</p>}
      </section>

      <footer className="footer">
        <p>API base: {API_BASE}</p>
      </footer>
    </div>
  );
}
