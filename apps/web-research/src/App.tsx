// apps/web-research/src/App.tsx
import { useState } from "react";
import AskPanel from "./components/AskPanel";
import FeedbackPanel from "./components/FeedbackPanel";
import ResearchConfig from "./components/ResearchConfig";
import StatsPanel from "./components/StatsPanel";
import type { AskResponse, ServedPolicy } from "./api/client";
import "./App.css";

export interface Config {
  served_policy: ServedPolicy;
  active_model_version: string;
  openai_model: string;
  gemini_model: string;
  temperature: number;
  max_tokens: number;
}

const DEFAULT_CONFIG: Config = {
  served_policy: "rule",
  active_model_version: "",
  openai_model: "gpt-4o-mini",
  gemini_model: "gemini-2.5-flash",
  temperature: 0.2,
  max_tokens: 512,
};

export default function App() {
  const [config, setConfig] = useState<Config>(DEFAULT_CONFIG);
  const [lastAsk, setLastAsk] = useState<AskResponse | null>(null);
  const [sessionLog, setSessionLog] = useState<AskResponse[]>([]);

  function handleAskSuccess(resp: AskResponse) {
    setLastAsk(resp);
    setSessionLog((prev) => [resp, ...prev]);
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔬 Research Console</h1>
        <span className="badge">multi-llm-answer-selection-ltr</span>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <ResearchConfig config={config} onChange={setConfig} />
          <StatsPanel />
        </aside>

        <main className="main-panel">
          <AskPanel config={config} onSuccess={handleAskSuccess} />
          {lastAsk && <FeedbackPanel askResp={lastAsk} />}
        </main>

        <aside className="log-panel">
          <h3>Session Log</h3>
          {sessionLog.length === 0 && <p className="muted">아직 질문 없음</p>}
          {sessionLog.map((r, i) => (
            <div key={i} className="log-entry" onClick={() => setLastAsk(r)}>
              <div className="log-qid">Q: {r.question_id.slice(0, 8)}…</div>
              <div className="log-summary muted">
                {r.selected_answer_summary.slice(0, 60)}…
              </div>
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
