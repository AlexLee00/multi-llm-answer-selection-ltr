// apps/web-research/src/components/AskPanel.tsx
import { useState, useEffect, useCallback } from "react";
import type { Config } from "../App";
import { postAsk } from "../api/client";
import type { AskResponse, Role, Level, Goal } from "../api/client";

/* ── 답변 전체 보기 모달 ── */
interface ModalProps {
  label: string;
  provider: string;
  answer: string;
  isWinner: boolean;
  onClose: () => void;
}

function AnswerModal({ label, provider, answer, isWinner, onClose }: ModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className={`modal-header ${isWinner ? "modal-header--winner" : ""}`}>
          <span className="modal-label">{label}</span>
          <span className="modal-provider">{provider}</span>
          {isWinner && <span className="winner-badge">⭐ 추천</span>}
          <button className="modal-close-btn" onClick={onClose} title="닫기 (ESC)">✕</button>
        </div>
        <div className="modal-body">
          <pre className="modal-answer">{answer || "(답변 없음)"}</pre>
        </div>
      </div>
    </div>
  );
}

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

  const [modal, setModal] = useState<"a" | "b" | null>(null);
  const closeModal = useCallback(() => setModal(null), []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setModal(null);
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

          <p className="click-hint">💡 카드를 클릭하면 전체 답변을 볼 수 있습니다</p>
          <div className="ab-compare">
            <div
              className={`candidate-card candidate-card--clickable ${result.served_choice_candidate_id === result.candidate_a_id ? "candidate-card--winner" : ""}`}
              onClick={() => setModal("a")}
              title="클릭하여 전체 답변 보기"
            >
              <div className="candidate-header">
                <span className="candidate-label">A</span>
                <span className="candidate-provider">{result.candidate_a_provider ?? "provider-a"}</span>
                {result.served_choice_candidate_id === result.candidate_a_id && (
                  <span className="winner-badge">⭐ 추천</span>
                )}
                <span className="expand-hint">🔍 전체보기</span>
              </div>
              <pre className="candidate-answer candidate-answer--preview">
                {result.candidate_a_answer ?? "(답변 없음)"}
              </pre>
              <div className="candidate-id muted">id: <code>{result.candidate_a_id.slice(0, 8)}…</code></div>
            </div>

            <div
              className={`candidate-card candidate-card--clickable ${result.served_choice_candidate_id === result.candidate_b_id ? "candidate-card--winner" : ""}`}
              onClick={() => setModal("b")}
              title="클릭하여 전체 답변 보기"
            >
              <div className="candidate-header">
                <span className="candidate-label">B</span>
                <span className="candidate-provider">{result.candidate_b_provider ?? "provider-b"}</span>
                {result.served_choice_candidate_id === result.candidate_b_id && (
                  <span className="winner-badge">⭐ 추천</span>
                )}
                <span className="expand-hint">🔍 전체보기</span>
              </div>
              <pre className="candidate-answer candidate-answer--preview">
                {result.candidate_b_answer ?? "(답변 없음)"}
              </pre>
              <div className="candidate-id muted">id: <code>{result.candidate_b_id.slice(0, 8)}…</code></div>
            </div>
          </div>
        </div>
      )}

      {modal === "a" && result && (
        <AnswerModal
          label="A"
          provider={result.candidate_a_provider ?? "provider-a"}
          answer={result.candidate_a_answer ?? ""}
          isWinner={result.served_choice_candidate_id === result.candidate_a_id}
          onClose={closeModal}
        />
      )}
      {modal === "b" && result && (
        <AnswerModal
          label="B"
          provider={result.candidate_b_provider ?? "provider-b"}
          answer={result.candidate_b_answer ?? ""}
          isWinner={result.served_choice_candidate_id === result.candidate_b_id}
          onClose={closeModal}
        />
      )}
    </section>
  );
}
