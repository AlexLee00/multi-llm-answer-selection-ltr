// apps/web-service/src/components/AnswerCard.tsx
import type { AskResponse } from "../api/client";

interface Props {
  resp: AskResponse;
  onNew: () => void;
}

export default function AnswerCard({ resp, onNew }: Props) {
  return (
    <div className="card">
      <h2>✅ AI 답변</h2>
      <pre className="answer-pre">{resp.selected_answer_summary}</pre>
      <div className="answer-meta">
        question_id: <code>{resp.question_id}</code>
      </div>
      <button className="btn-outline" onClick={onNew}>
        ＋ 새 질문
      </button>
    </div>
  );
}
