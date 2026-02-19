// apps/web-research/src/components/FeedbackPanel.tsx
import { useState } from "react";
import { postFeedback } from "../api/client";
import type { AskResponse, UserChoice } from "../api/client";

interface Props {
  askResp: AskResponse;
}

const CHOICES: { value: UserChoice; label: string }[] = [
  { value: "a", label: "A가 더 좋다" },
  { value: "b", label: "B가 더 좋다" },
  { value: "tie", label: "비슷하다" },
  { value: "bad", label: "둘 다 나쁨" },
];

const REASON_TAGS = [
  "clarity", "correctness", "has_steps", "has_code",
  "concise", "detailed", "practical", "relevant",
];

export default function FeedbackPanel({ askResp }: Props) {
  const [choice, setChoice] = useState<UserChoice | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleTag(tag: string) {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!choice) return;
    setLoading(true);
    setError(null);
    try {
      await postFeedback({
        question_id: askResp.question_id,
        candidate_a_id: askResp.candidate_a_id,
        candidate_b_id: askResp.candidate_b_id,
        user_choice: choice,
        reason_tags: tags.length > 0 ? tags : undefined,
        note: note || undefined,
      });
      setDone(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <section className="card">
        <h2>✅ Feedback 제출 완료</h2>
        <p className="muted">question_id: <code>{askResp.question_id}</code></p>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>📝 Feedback</h2>

      {/* 답변 미리보기: 피드백 전에 A/B 내용 확인 */}
      {(askResp.candidate_a_answer || askResp.candidate_b_answer) && (
        <div className="ab-compare ab-compare--compact">
          <div className={`candidate-card ${askResp.served_choice_candidate_id === askResp.candidate_a_id ? "candidate-card--winner" : ""}`}>
            <div className="candidate-header">
              <span className="candidate-label">A</span>
              <span className="candidate-provider">{askResp.candidate_a_provider ?? "provider-a"}</span>
              {askResp.served_choice_candidate_id === askResp.candidate_a_id && (
                <span className="winner-badge">⭐ 추천</span>
              )}
            </div>
            <pre className="candidate-answer candidate-answer--compact">{askResp.candidate_a_answer ?? "(없음)"}</pre>
          </div>
          <div className={`candidate-card ${askResp.served_choice_candidate_id === askResp.candidate_b_id ? "candidate-card--winner" : ""}`}>
            <div className="candidate-header">
              <span className="candidate-label">B</span>
              <span className="candidate-provider">{askResp.candidate_b_provider ?? "provider-b"}</span>
              {askResp.served_choice_candidate_id === askResp.candidate_b_id && (
                <span className="winner-badge">⭐ 추천</span>
              )}
            </div>
            <pre className="candidate-answer candidate-answer--compact">{askResp.candidate_b_answer ?? "(없음)"}</pre>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Choice */}
        <label>어느 답변이 더 좋았나요? *</label>
        <div className="choice-group">
          {CHOICES.map((c) => (
            <button
              key={c.value}
              type="button"
              className={`choice-btn ${choice === c.value ? "active" : ""}`}
              onClick={() => setChoice(c.value)}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Reason tags */}
        <label>이유 태그 (선택)</label>
        <div className="tag-group">
          {REASON_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              className={`tag-btn ${tags.includes(tag) ? "active" : ""}`}
              onClick={() => toggleTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>

        {/* Note */}
        <label>메모 (선택)</label>
        <textarea
          rows={2}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="자유 기술..."
        />

        {error && <div className="error-box">❌ {error}</div>}

        <button type="submit" disabled={!choice || loading}>
          {loading ? "⏳ 제출 중…" : "📤 Feedback 제출"}
        </button>
      </form>
    </section>
  );
}
