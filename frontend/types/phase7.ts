import type { UserOption } from "@/types/phase2";
import type { Guest } from "@/types/phase6";

export type AIStatus = { enabled: boolean; model: string };

export type QnA = {
  id: string;
  release_id: string;
  guest: Guest | null;
  question: string;
  ai_answer: string | null;
  supervisor_answer: string | null;
  pjk_answer: string | null;
  final_answer: string | null;
  ai_model: string | null;
  ai_sources: string[];
  generated_at: string | null;
  finalizer: UserOption | null;
  finalized_at: string | null;
  created_at: string;
  updated_at: string;
};

export type MinutesForm = {
  opening: string | null;
  discussion: string | null;
  notes: string | null;
  conclusion: string | null;
};

export type Minutes = MinutesForm & {
  id: string;
  release_id: string;
  content: string | null;
  docx_ready: boolean;
  pdf_ready: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
};

