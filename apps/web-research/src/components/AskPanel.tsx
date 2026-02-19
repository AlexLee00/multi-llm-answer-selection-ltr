// apps/web-research/src/components/AskPanel.tsx
import { useState } from "react";
import type { Config } from "../App";
import { postAsk } from "../api/client";
import type { AskResponse, Role, Level, Goal } from "../api/client";

interface Props {
  config: Config;
  onSuccess: (resp: AskResponse) => void;
}

const ROLES: Role[] = ["planner", "designer", "dev", "tester", "other"];
const LEVELS: Level[] = ["beginner", "intermediate", "advanced"];
const GOALS: Goal[] = ["concept", "practice", "assignment", "interview", "other"];

export default function AskPanel({ config, onSuccess }: Props) {
  const [role, setRole] = useState<Role>("dev");
  const [level, setLevel] = useState<Level>("beginner");
  const [goal, setGoal] = useState<Goal>("practice");
  const [stack, setStack] = useState("python, fastapi");
  const [constraints, setConstraints] = useState("");
  const [question, setQuestion] = useState("");
  const [domain, setDomain] = useState("backend");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await postAsk({
        user: { role, level },
        context: { goal, stack, constraints },
        question,
        domain,
        _served_policy: config.served_policy,
        _active_model_version: config.active_model_version || undefined,
      });
      setResult(resp);
      onSuccess(resp);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h2>💬 Ask</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div>
            <label>Role</label>
            <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
              {ROLES.map((r) => <option key={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label>Level</label>
            <select value={level} onChange={(e) => setLevel(e.target.value as Level)}>
              {LEVELS.map((l) => <option key={l}>{l}</option>)}
            </select>
          </div>
          <div>
            <label>Goal</label>
            <select value={goal} onChange={(e) => setGoal(e.target.value as Goal)}>
              {GOALS.map((g) => <option key={g}>{g}</option>)}
            </select>
          </div>
        </div>

        <label>Stack</label>
        <input value={stack} onChange={(e) => setStack(e.target.value)} placeholder="python, fastapi" />

        <label>Constraints</label>
        <input value={constraints} onChange={(e) => setConstraints(e.target.value)} placeholder="windows, no admin" />

        <label>Domain</label>
        <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="backend" />

        <label>Question</label>
        <textarea
          rows={4}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="질문을 입력하세요..."
          required
        />

        {/* Config summary */}
        <div className="config-summary muted">
          policy: <strong>{config.served_policy}</strong>
          {" | "}model: <strong>{config.active_model_version || "latest"}</strong>
          {" | "}temp: <strong>{config.temperature}</strong>
          {" | "}max_tokens: <strong>{config.max_tokens}</strong>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "⏳ 생성 중…" : "▶ Ask"}
        </button>
      </form>

      {error && <div className="error-box">❌ {error}</div>}

      {result && (
        <div className="result-box">
          <div className="result-meta">
            <span>question_id: <code>{result.question_id}</code></span>
            {" | "}
            <span>추천: <strong>{result.served_choice_candidate_id === result.candidate_a_id ? "A" : "B"} 선택됨</strong></span>
          </div>

          {/* A/B 두 답변 나란히 표시 */}
          <div className="ab-compare">
            {/* 후보 A */}
            <div className={`candidate-card ${result.served_choice_candidate_id === result.candidate_a_id ? "candidate-card--winner" : ""}`}>
              <div className="candidate-header">
                <span className="candidate-label">A</span>
                <span className="candidate-provider">{result.candidate_a_provider ?? "provider-a"}</span>
                {result.served_choice_candidate_id === result.candidate_a_id && (
                  <span className="winner-badge">⭐ 추천</span>
                )}
              </div>
              <pre className="candidate-answer">{result.candidate_a_answer ?? "(답변 없음)"}</pre>
              <div className="candidate-id muted">id: <code>{result.candidate_a_id.slice(0, 8)}…</code></div>
            </div>

            {/* 후보 B */}
            <div className={`candidate-card ${result.served_choice_candidate_id === result.candidate_b_id ? "candidate-card--winner" : ""}`}>
              <div className="candidate-header">
                <span className="candidate-label">B</span>
                <span className="candidate-provider">{result.candidate_b_provider ?? "provider-b"}</span>
                {result.served_choice_candidate_id === result.candidate_b_id && (
                  <span className="winner-badge">⭐ 추천</span>
                )}
              </div>
              <pre className="candidate-answer">{result.candidate_b_answer ?? "(답변 없음)"}</pre>
              <div className="candidate-id muted">id: <code>{result.candidate_b_id.slice(0, 8)}…</code></div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
