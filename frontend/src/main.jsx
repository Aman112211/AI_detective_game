import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function readJsonResponse(response) {
  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`Server returned an invalid response (${response.status}).`);
  }
}

function App() {
  const [screen, setScreen] = useState("start");
  const [selectedMode, setSelectedMode] = useState("pirate");
  const [caseData, setCaseData] = useState(null);
  const [sessionId, setSessionId] = useState("");
  const [questionsRemaining, setQuestionsRemaining] = useState(15);
  const [messages, setMessages] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [draft, setDraft] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [score, setScore] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pirateTalking, setPirateTalking] = useState(false);

  async function startCase() {
    setBusy(true); setError("");
    try {
      const response = await fetch(`${API_URL}/api/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: selectedMode }),
      });
      const data = await readJsonResponse(response);
      if (!response.ok) throw new Error((data && data.error) || "Could not open the case.");
      setCaseData(data); setSessionId(data.sessionId); setQuestionsRemaining(data.questionsRemaining); setScreen("briefing");
    } catch (requestError) { setError(requestError.message); } finally { setBusy(false); }
  }

  async function askQuestion(event) {
    event.preventDefault(); if (!draft.trim() || busy) return;
    const question = draft.trim(); setDraft(""); setBusy(true); setError("");
    setPirateTalking(true);
    try {
      const response = await fetch(`${API_URL}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId, message: question }) });
      const data = await readJsonResponse(response);
      if (!response.ok) throw new Error((data && data.error) || "The detective could not answer.");
      setMessages((current) => [...current, { role: "player", text: question }, { role: "detective", text: data.response }]);
      setQuestionsRemaining(data.questionsRemaining); setEvidence((current) => [...current, ...(data.newEvidence || [])]);
    } catch (requestError) { setError(requestError.message); } finally {
      setBusy(false);
      setPirateTalking(false);
    }
  }

  async function submitAccusation(event) {
    event.preventDefault(); const form = new FormData(event.currentTarget); setBusy(true); setError("");
    try {
      const response = await fetch(`${API_URL}/api/submit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId, culprit: form.get("culprit"), method: form.get("method"), motive: form.get("motive"), evidence: form.getAll("evidence") }) });
      const data = await readJsonResponse(response); if (!response.ok) throw new Error((data && data.error) || "Could not submit accusation.");
      setScore(data); setModalOpen(false); setScreen("score");
    } catch (requestError) { setError(requestError.message); } finally { setBusy(false); }
  }

  if (screen === "start") return <StartScreen selectedMode={selectedMode} onModeChange={setSelectedMode} onStart={startCase} busy={busy} error={error} />;
  if (screen === "briefing") return <Briefing caseData={caseData} onContinue={() => setScreen("investigate")} />;
  if (screen === "score") return <ScoreScreen score={score} onRestart={() => window.location.reload()} />;

  return <main className="app-shell">
    <header className="topbar"><div className="brand"><span className="brand-mark">AD</span><span>AI Detective</span></div><div className="case-label">CASE 001 / {caseData.title}</div><div className="counter"><span>QUESTIONS LEFT</span><strong>{questionsRemaining}</strong></div></header>
    <div className="workspace">
      <aside className="suspect-board panel"><SectionTitle eyebrow="THE CREW" title="Suspect board" /><div className="suspect-list">{caseData.suspects.map((suspect) => <article className="suspect" key={suspect.id}><div className={`initial initial-${suspect.id}`}>{suspect.name.split(" ").map((word) => word[0]).join("")}</div><div><h3>{suspect.name}</h3><p>{suspect.bio}</p><span className="suspicion">{suspect.initialSuspicion.replace("_", " ")}</span></div></article>)}</div></aside>
      <section className="detective-column"><div className="detective-area panel"><div className="lamp-glow" /><CharacterDisplay selectedMode={selectedMode} talking={pirateTalking} /><div className="detective-copy"><span className="eyebrow">FIRST MATE SALTY SABLE</span><h1>Ask the right question.</h1><p>“The sea keeps its secrets, detective. We’ll see which ones this crew forgot to bury.”</p></div></div><div className="chat panel"><SectionTitle eyebrow="INTERROGATION LOG" title="Question the detective" /><div className="transcript">{messages.length === 0 && <div className="empty-log">Your questions will appear here. Choose your words carefully.</div>}{messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><span>{message.role === "player" ? "YOU" : "SALTY SABLE"}</span><p>{message.text}</p></div>)}</div><form className="question-form" onSubmit={askQuestion}><input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask about a suspect, clue, or moment..." disabled={busy || questionsRemaining === 0} /><button type="submit" disabled={busy || !draft.trim()}>SEND <span>↗</span></button></form>{error && <p className="error">{error}</p>}</div></section>
      <aside className="evidence-board panel"><SectionTitle eyebrow="CASE FILE" title="Evidence" /><div className="evidence-list">{evidence.length === 0 ? <div className="empty-evidence">No evidence pinned yet.<br />Ask precise questions to reveal the file.</div> : evidence.map((item) => <article className="evidence" key={item.id}><span className="evidence-tag">{item.category}</span><h3>{item.name}</h3><p>{item.description}</p></article>)}</div><button className="accuse-button" onClick={() => setModalOpen(true)}>MAKE ACCUSATION <span>→</span></button></aside>
    </div>{modalOpen && <AccusationModal suspects={caseData.suspects} evidence={evidence} onClose={() => setModalOpen(false)} onSubmit={submitAccusation} busy={busy} />}
  </main>;
}

function CharacterDisplay({ selectedMode, talking }) {
  if (selectedMode === "pirate") return <PirateCharacter talking={talking} />;
  return <PlaceholderDetective />;
}

function PirateCharacter({ talking }) {
  const idleLayers = [
    { key: "body", src: new URL("./assets/pirate/body.png", import.meta.url).href },
    { key: "head", src: new URL("./assets/pirate/head.png", import.meta.url).href },
    { key: "left_hand", src: new URL("./assets/pirate/left_hand.png", import.meta.url).href },
    { key: "right_hand", src: new URL("./assets/pirate/right_hand.png", import.meta.url).href },
    { key: "hat", src: new URL("./assets/pirate/hat.png", import.meta.url).href },
  ];

  const mouthFrames = [
    { key: "mouth_closed", src: new URL("./assets/pirate/mouth_closed.png", import.meta.url).href },
    { key: "mouth_half_open", src: new URL("./assets/pirate/mouth_half_open.png", import.meta.url).href },
    { key: "mouth_full_open", src: new URL("./assets/pirate/mouth_full_open.png", import.meta.url).href },
    { key: "mouth_half_open_alt", src: new URL("./assets/pirate/mouth_half_open.png", import.meta.url).href },
  ];

  const [mouthIndex, setMouthIndex] = useState(0);

  useEffect(() => {
    if (!talking) {
      setMouthIndex(0);
      return;
    }

    const intervalId = setInterval(() => {
      setMouthIndex((current) => (current + 1) % mouthFrames.length);
    }, 110);

    return () => clearInterval(intervalId);
  }, [talking]);

  const visibleLayers = talking
    ? [
        ...idleLayers.slice(0, 4),
        mouthFrames[mouthIndex],
        idleLayers[4],
      ]
    : idleLayers;

  return (
    <div className="character-puppet pirate-character" aria-label="Pirate detective">
      {visibleLayers.map((layer) => (
        <img key={layer.key} className="character-layer" src={layer.src} alt="" />
      ))}
    </div>
  );
}

function SectionTitle({ eyebrow, title }) { return <div className="section-title"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>; }
function PlaceholderDetective() { return <div className="placeholder-detective"><div className="hat" /><div className="face"><span>◒</span><span>◒</span><i /></div><div className="coat" /></div>; }
function StartScreen({ selectedMode, onModeChange, onStart, busy, error }) {
  const modes = [
    { value: "pirate", label: "Pirate Case", subtitle: "The Vanished Doubloons" },
    { value: "noir", label: "Noir Case", subtitle: "The Ashport Ledger Murder" },
  ];

  return <main className="start-screen"><div className="start-copy"><span className="eyebrow">A LIMITED INQUIRY / AN UNLIMITED SEA</span><h1>AI<br /><em>Detective</em></h1><p>Choose your case and follow the clues through a locked room, a storm-tossed ship, or a rain-soaked newsroom.</p><div className="mode-select"><div className="mode-label">Choose game mode</div><div className="mode-options">{modes.map((mode) => <button type="button" key={mode.value} className={`mode-option ${selectedMode === mode.value ? "active" : ""}`} onClick={() => onModeChange(mode.value)}>{mode.label}<small>{mode.subtitle}</small></button>)}</div></div><button className="primary-button" onClick={onStart} disabled={busy}>OPEN THE CASE <span>→</span></button>{error && <p className="error">{error}</p>}</div><div className="start-art"><div className="moon" /><div className="ship-line" /><CharacterDisplay selectedMode={selectedMode} /><span className="art-caption">{selectedMode === "pirate" ? "FIRST MATE\n" : "PRIVATE EYE\n"}<b>{selectedMode === "pirate" ? "SALTY SABLE" : "VIC MARLOWE"}</b></span></div></main>;
}
function Briefing({ caseData, onContinue }) { return <main className="briefing-screen"><div className="briefing-paper"><span className="eyebrow">THE CRIMSON GULL / NIGHT WATCH</span><h1>{caseData.title}</h1><div className="rule" /><p className="briefing-text">{caseData.briefing}</p><div className="briefing-meta"><span><b>04</b> SUSPECTS</span><span><b>15</b> QUESTIONS</span><span><b>01</b> CASE FILE</span></div><button className="primary-button" onClick={onContinue}>BEGIN INQUIRY <span>→</span></button></div></main>; }
function AccusationModal({ suspects, evidence, onClose, onSubmit, busy }) { return <div className="modal-backdrop"><form className="modal" onSubmit={onSubmit}><button type="button" className="close" onClick={onClose}>×</button><span className="eyebrow">FINAL STATEMENT</span><h2>Who took the doubloons?</h2><label>CULPRIT<select name="culprit" required><option value="">Select a suspect</option>{suspects.map((suspect) => <option value={suspect.id} key={suspect.id}>{suspect.name}</option>)}</select></label><label>METHOD<textarea name="method" required placeholder="How was the theft carried out?" /></label><label>MOTIVE<textarea name="motive" required placeholder="Why would they risk it?" /></label><fieldset><legend>SUPPORTING EVIDENCE</legend>{evidence.length === 0 ? <small>No discovered evidence yet.</small> : evidence.map((item) => <label className="check" key={item.id}><input type="checkbox" name="evidence" value={item.id} /> {item.name}</label>)}</fieldset><button className="primary-button" disabled={busy}>SUBMIT ACCUSATION <span>→</span></button></form></div>; }
function ScoreScreen({ score, onRestart }) { return <main className="score-screen"><span className="eyebrow">CASE REPORT / FINAL ENTRY</span><h1>{score?.gameStatus === "solved" ? "Case Closed." : "The trail goes cold."}</h1><div className="score-number">{score?.score ?? 0}<small>/ 25</small></div><div className="score-breakdown">{Object.entries(score?.breakdown || {}).map(([label, value]) => <div key={label}><span>{label}</span><b>{value} pts</b></div>)}</div><button className="primary-button" onClick={onRestart}>RETURN TO DESK <span>↻</span></button></main>; }

createRoot(document.getElementById("root")).render(<App />);