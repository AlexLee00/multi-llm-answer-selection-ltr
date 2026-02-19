// apps/web-service/src/components/FeedbackBar.tsx
import { useState } from "react";
import { postFeedback } from "../api/client";
import type { AskResponse, UserChoice } from "../api/client";

interface Props {
  askResp: AskResponse;
  onDone: () => void;
}

const CHOICES: { value: UserChoice; label: string; emoji: string }[] = [
  { value: "a",   label: "A가 더 좋음",  emoji: "👍" },
  { value: "b",   label: "B가 더 좋음",  emoji: "👍" },
  { value: "tie", label: "비슷함",        emoji: "🤝" },
  { value: "bad", label: "둘 다 별로",    emoji: "👎" },
];

export default function FeedbackBar({ askResp, onDone }: Props) {
  const [choice, setChoice] = useState<UserChoice | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  async function handleSubmit(selected: UserChoice) {
    setChoice(selected);
    setLoading(true);
    setError(null);
    try {
      await postFeedback({
        question_id:   askResp.question_id,
        candidate_a_id: askResp.candidate_a_id,
        candidate_b_id: askResp.candidate_b_id,
        user_choice: selected,
      });
      onDone();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? String(err);
      setError(msg);
      setChoice(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feedback-bar">
      <h3>이 답변이 도움이 됐나요? (선택)</h3>
      <div className="choice-group">
        {CHOICES.map((c) => (
          <button
            key={c.value}
            className={`choice-btn ${choice === c.value ? "active" : ""}`}
            disabled={loading}
            onClick={() => handleSubmit(c.value)}
          >
            {c.emoji} {c.label}
          </button>
        ))}
      </div>
      {error && <div className="error-box">❌ {error}</div>}
    </div>
  );
}
