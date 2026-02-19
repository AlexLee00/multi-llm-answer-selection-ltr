// apps/web-research/src/api/client.ts
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
export type ServedPolicy = "rule" | "ltr";

export interface AskParams {
  user: { role: Role; level: Level };
  context: { goal: Goal; stack: string; constraints: string };
  question: string;
  domain: string;
  // Research-only: override policy & model version per request
  _served_policy?: ServedPolicy;
  _active_model_version?: string;
}

export interface AskResponse {
  question_id: string;
  selected_candidate_id: string;
  selected_answer_summary: string;
  candidate_a_id: string;
  candidate_b_id: string;
  served_choice_candidate_id: string;
  // Full answer texts for comparison view
  candidate_a_answer?: string;
  candidate_b_answer?: string;
  candidate_a_provider?: string;
  candidate_b_provider?: string;
}

export interface FeedbackParams {
  question_id: string;
  candidate_a_id: string;
  candidate_b_id: string;
  user_choice: UserChoice;
  reason_tags?: string[];
  note?: string;
}

export interface FeedbackResponse {
  feedback_id: string;
}

export interface ModelRecord {
  model_version: string;
  feature_version: string;
  metrics_json: Record<string, unknown>;
  artifact_path: string;
  trained_at: string;
}

export interface StatsResponse {
  total_feedbacks: number;
  rule_served: number;
  ltr_served: number;
  today_feedbacks: number;
}

// ─── API calls ────────────────────────────────────────────────────────────────

export async function postAsk(params: AskParams): Promise<AskResponse> {
  const { _served_policy, _active_model_version, ...body } = params;
  const res = await api.post<AskResponse>("/api/v1/ask", body, {
    headers: {
      ...((_served_policy) && { "X-Served-Policy": _served_policy }),
      ...((_active_model_version) && { "X-Model-Version": _active_model_version }),
    },
  });
  return res.data;
}

export async function postFeedback(params: FeedbackParams): Promise<FeedbackResponse> {
  const res = await api.post<FeedbackResponse>("/api/v1/feedback", params);
  return res.data;
}

export async function fetchModels(): Promise<ModelRecord[]> {
  const res = await api.get<ModelRecord[]>("/api/v1/admin/models");
  return res.data;
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await api.get<StatsResponse>("/api/v1/admin/stats");
  return res.data;
}
