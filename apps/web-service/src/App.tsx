// apps/web-service/src/App.tsx
import { useState } from "react";
import AskForm from "./components/AskForm";
import AnswerCard from "./components/AnswerCard";
import FeedbackBar from "./components/FeedbackBar";
import type { AskResponse } from "./api/client";
import "./App.css";

export default function App() {
  const [askResp, setAskResp] = useState<AskResponse | null>(null);
  const [feedbackDone, setFeedbackDone] = useState(false);

  function handleAsk(resp: AskResponse) {
    setAskResp(resp);
    setFeedbackDone(false);
  }

  function handleNewQuestion() {
    setAskResp(null);
    setFeedbackDone(false);
  }

  return (
    <div className="page">
      <header className="top-bar">
        <span className="logo-text">⚡ LLM Q&A</span>
        <span className="subtitle">AI가 최적 답변을 선택합니다</span>
      </header>

      <main className="content">
        {!askResp ? (
          <AskForm onSuccess={handleAsk} />
        ) : (
          <>
            <AnswerCard resp={askResp} onNew={handleNewQuestion} />
            {!feedbackDone && (
              <FeedbackBar askResp={askResp} onDone={() => setFeedbackDone(true)} />
            )}
            {feedbackDone && (
              <p className="feedback-thanks">✅ 피드백 감사합니다!</p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
