import type { UserOption } from "@/types/phase2";

export type CheckType = "data_consistency" | "document_coverage" | "cross_document" | "language";
export type CheckSeverity = "error" | "warning" | "suggestion";
export type ReviewAction = "fixed" | "confirmed_correct" | "ignored";

export type CheckReview = {
  id: string;
  action: ReviewAction;
  note: string | null;
  reviewer: UserOption;
  created_at: string;
};

export type CheckResult = {
  id: string;
  run_id: string;
  document_id: string | null;
  document_type: string | null;
  document_name: string | null;
  brs_data_id: string | null;
  check_type: CheckType;
  severity: CheckSeverity;
  field_name: string | null;
  expected_value: string | null;
  actual_value: string | null;
  message: string;
  suggestion: string | null;
  status: "open" | "resolved" | "confirmed" | "ignored";
  page_number: number | null;
  context_text: string | null;
  comparison_values: Record<
    string,
    {
      label: string;
      value: string | null;
      page_number: number | null;
      section_label: string | null;
      context: string | null;
      document_id: string | null;
      status?: "match" | "different" | "needs_verification";
      value_kind?: "point" | "range";
      basis?: string | null;
      subject?: string | null;
      role?: string;
    }
  > | null;
  reviews: CheckReview[];
  created_at: string;
  updated_at: string;
};

export type CheckRun = {
  id: string;
  brs_id: string;
  status: string;
  engine_version: string;
  total_checks: number;
  passed_checks: number;
  error_count: number;
  warning_count: number;
  suggestion_count: number;
  data_consistency_score: string | number;
  cross_document_score: string | number;
  language_score: string | number;
  overall_score: string | number;
  initiator: UserOption;
  started_at: string;
  completed_at: string | null;
};

export type CheckRunDetail = CheckRun & { results: CheckResult[] };
