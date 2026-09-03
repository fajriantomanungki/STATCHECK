import type { UserOption } from "@/types/phase2";

export type ReleaseBRS = {
  id: string;
  kode_brs: string;
  nama_brs: string;
  waktu_rilis: string;
  fungsi_pj: string;
  status: string;
};

export type GuestForm = {
  nama: string;
  instansi: string;
  jabatan: string | null;
  nomor_hp: string | null;
  email: string | null;
};

export type Guest = GuestForm & {
  id: string;
  release_id: string;
  created_at: string;
  updated_at: string;
};

export type ReleaseForm = {
  tanggal_rilis: string;
  waktu_rilis: string;
  tempat: string;
  judul_rilis: string;
  brs_ids: string[];
};

export type Release = {
  id: string;
  kode_rilis: string;
  tanggal_rilis: string;
  waktu_rilis: string;
  tempat: string;
  judul_rilis: string;
  status: "draft" | "ongoing" | "completed";
  creator: UserOption;
  jumlah_brs: number;
  jumlah_tamu: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ReleaseDetail = Release & { brs: ReleaseBRS[]; guests: Guest[] };

