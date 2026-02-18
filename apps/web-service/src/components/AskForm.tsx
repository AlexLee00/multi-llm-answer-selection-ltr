// apps/web-service/src/components/AskForm.tsx
import { useState } from "react";
import { postAsk } from "../api/client";
import type { AskResponse, Role, Level, Goal } from "../api/client";

interface Props {
  onSuccess: (resp: AskResponse) => void;
}

const ROLES: { value: Role; label: string }[] = [
  { value: "planner",  label: "기획자" },
  { value: "designer", label: "디자이너" },
  { value: "dev",      label: "개발자" },
  { value: "tester",   label: "테스터" },
  { value: "other",    label: "기타" },
];

const LEVELS: { value: Level; label: string }[] = [
  { value: "beginner",     label: "입문" },
  { value: "intermediate", label: "중급" },
  { value: "advanced",     label: "고급" },
];

const GOALS: { value: Goal; label: string }[] = [
  { value: "concept",    label: "개념 이해" },
  { value: "practice",   label: "실습" },
  { value: "assignment", label: "과제" },
  { value: "interview",  label: "면접 준비" },
  { value: "other",      label: "기타" },
];

export default function AskForm({ onSuccess }: Props) {
  const [role, setRole]   = useState<Role>("dev");
  const [level, setLevel] = useState<Level>("beginner");
  const [goal, setGoal]   = useState<Goal>("practice");
  const [stack, setStack] = useState("python, fastapi");
  const [question, setQuestion] = useState("");
  const [domain, setDomain] = useState("backend");

  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await postAsk({
        user: { role, level },
        context: { goal, stack },
        question: question.trim(),
        domain,
      });
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
    <div className="card">
      <h2>💬 질문하기</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div>
            <label>역할</label>
            <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
              {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>
          <div>
            <label>수준</label>
            <select value={level} onChange={(e) => setLevel(e.target.value as Level)}>
              {LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
          <div>
            <label>목적</label>
            <select value={goal} onChange={(e) => setGoal(e.target.value as Goal)}>
              {GOALS.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
            </select>
          </div>
        </div>

        <label>기술 스택</label>
        <input
          value={stack}
          onChange={(e) => setStack(e.target.value)}
          placeholder="python, fastapi, react..."
        />

        <label>도메인</label>
        <input
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="backend / frontend / ml..."
        />

        <label>질문 *</label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="궁금한 내용을 입력하세요..."
          required
        />

        {error && <div className="error-box">❌ {error}</div>}

        <button className="btn-primary" type="submit" disabled={loading || !question.trim()}>
          {loading ? "⏳ AI 답변 생성 중…" : "▶ 답변 받기"}
        </button>
      </form>
    </div>
  );
}
