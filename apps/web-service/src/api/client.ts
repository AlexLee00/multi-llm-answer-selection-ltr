// apps/web-service/src/api/client.ts
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ─── Types ────────────────────────────────────────────────────────────────────

export type Role = "planner" | "designer" | "dev" | "tester" | "other";
export type Level = "beginner" | "intermediate" | "advanced";
export type Goal = "concept" | "practice" | "assignment" | "interview" | "other";
export type UserChoice = "a" | "b" | "tie" | "bad";

export interface AskParams {
  user: { role: Role; level: Level };
  context: { goal: Goal; stack?: string; constraints?: string };
  question: string;
  domain: string;
}

export interface AskResponse {
  question_id: string;
  selected_candidate_id: string;
  selected_answer_summary: string;
  candidate_a_id: string;
  candidate_b_id: string;
  served_choice_candidate_id: string;
}

export interface FeedbackParams {
  question_id: string;
  candidate_a_id: string;
  candidate_b_id: string;
  user_choice: UserChoice;
  reason_tags?: string[];
  note?: string;
}

// ─── API calls ────────────────────────────────────────────────────────────────

export async function postAsk(params: AskParams): Promise<AskResponse> {
  const res = await api.post<AskResponse>("/api/v1/ask", params);
  return res.data;
}

export async function postFeedback(params: FeedbackParams): Promise<void> {
  await api.post("/api/v1/feedback", params);
}
