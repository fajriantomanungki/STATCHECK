import type { User } from "@/types/auth";

export type UserOption = Pick<User, "id" | "nama" | "nik" | "user_level" | "fungsi">;

export type Indicator = {
  id: string;
  nama_indikator: string;
  kategori: string;
  satuan_default: string;
  fungsi: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TeamMember = { id: string; role: string; user: UserOption };

export type BRS = {
  id: string; kode_brs: string; nama_brs: string; waktu_rilis: string;
  fungsi_pj: string; status: string; pjk: UserOption; supervisor: UserOption | null;
  team?: TeamMember[]; jumlah_data: number; created_at: string; updated_at?: string;
};

export type BRSForm = {
  nama_brs: string; waktu_rilis: string; fungsi_pj: string;
  supervisor_id: string | null; team_user_ids: string[];
};

export type BRSDataForm = {
  indicator_id: string; sub_indikator: string | null; periode_data: string;
  deskripsi_periode: string; nilai_data: string; satuan: string;
  analisis: string | null; fenomena: string | null;
};

export type BRSData = BRSDataForm & {
  id: string; brs_id: string; indicator: Indicator; created_by: string;
  created_at: string; updated_at: string;
};

export type DashboardSummary = {
  total_brs: number; draft_brs: number; total_indicators: number; total_brs_data: number;
};
