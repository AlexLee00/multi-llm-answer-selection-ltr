// apps/web-service/src/components/AnswerCard.tsx
import { useState, useEffect, useCallback } from "react";
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

/* 전체 답변 모달 */
function AnswerModal({ text, onClose }: { text: string; onClose: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="svc-modal-backdrop" onClick={onClose}>
      <div className="svc-modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="svc-modal-header">
          <span className="svc-modal-title">AI 추천 답변 전체보기</span>
          <button className="svc-modal-close" onClick={onClose} title="닫기 (ESC)">X</button>
        </div>
        <div className="svc-modal-body">
          <div className="answer-body">{renderAnswer(text)}</div>
        </div>
      </div>
    </div>
  );
}

export default function AnswerCard({ resp, onNew }: Props) {
  const answerText = resp.selected_answer_summary;
  const [showModal, setShowModal] = useState(false);
  const closeModal = useCallback(() => setShowModal(false), []);

  return (
    <div className="card">
      <h2>AI 추천 답변</h2>

      {answerText ? (
        <>
          <div
            className="answer-preview-wrap"
            onClick={() => setShowModal(true)}
            title="클릭하여 전체 답변 보기"
          >
            <div className="answer-body answer-body--preview">
              {renderAnswer(answerText)}
            </div>
            <div className="answer-expand-bar">전체 답변 보기</div>
          </div>
        </>
      ) : (
        <p className="muted">답변을 불러오지 못했습니다.</p>
      )}

      <div className="answer-meta">
        question_id: <code>{resp.question_id}</code>
      </div>
      <button className="btn-outline" onClick={onNew}>
        + 새 질문
      </button>

      {showModal && answerText && (
        <AnswerModal text={answerText} onClose={closeModal} />
      )}
    </div>
  );
}
