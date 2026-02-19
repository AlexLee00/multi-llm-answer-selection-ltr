// apps/web-service/src/components/AnswerCard.tsx
import type { AskResponse } from "../api/client";

interface Props {
  resp: AskResponse;
  onNew: () => void;
}

/** 코드블록(```) 기준으로 텍스트/코드 분리 렌더링 */
function renderAnswer(text: string) {
  const parts = text.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const inner = part.slice(3, -3).replace(/^\w*\n/, "");
      return <pre key={i} className="code-block">{inner}</pre>;
    }
    return (
      <p key={i} className="answer-paragraph">
        {part.split("\n").map((line, j, arr) => (
          <span key={j}>
            {line}
            {j < arr.length - 1 && <br />}
          </span>
        ))}
      </p>
    );
  });
}

export default function AnswerCard({ resp, onNew }: Props) {
  const answerText = resp.selected_answer_summary;

  return (
    <div className="card">
      <h2>✅ AI 추천 답변</h2>

      {answerText ? (
        <div className="answer-body">
          {renderAnswer(answerText)}
        </div>
      ) : (
        <p className="muted">답변을 불러오지 못했습니다.</p>
      )}

      <div className="answer-meta">
        question_id: <code>{resp.question_id}</code>
      </div>
      <button className="btn-outline" onClick={onNew}>
        ＋ 새 질문
      </button>
    </div>
  );
}
