import type { UserOption } from "@/types/phase2";

export type ApprovalEvent = {
  id: string;
  approval_level: "pjk" | "supervisor" | "ka_bps";
  action: string;
  from_status: string;
  to_status: string;
  note: string | null;
  user: UserOption;
  created_at: string;
};

export type ApprovalWorkflow = {
  brs_id: string;
  current_status: string;
  latest_check_id: string | null;
  latest_score: string | null;
  open_findings: number;
  error_count: number;
  warning_count: number;
  suggestion_count: number;
  events: ApprovalEvent[];
};

