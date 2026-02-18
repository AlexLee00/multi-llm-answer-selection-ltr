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
          </div>
          <div className="answer-box">
            <h4>Selected Answer</h4>
            <pre>{result.selected_answer_summary}</pre>
          </div>
          <div className="candidate-ids muted">
            <div>candidate_a: <code>{result.candidate_a_id}</code></div>
            <div>candidate_b: <code>{result.candidate_b_id}</code></div>
            <div>served: <code>{result.served_choice_candidate_id}</code></div>
          </div>
        </div>
      )}
    </section>
  );
}
