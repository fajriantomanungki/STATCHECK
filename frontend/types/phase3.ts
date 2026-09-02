import type { UserOption } from "@/types/phase2";

export type DocumentType = "bahan_publikasi" | "bahan_paparan" | "narasi_pimpinan";

export type DocumentContent = {
  id: string;
  page_number: number;
  section_label: string;
  text_content: string;
};

export type BRSDocument = {
  id: string;
  brs_id: string;
  document_type: DocumentType;
  file_name: string;
  file_extension: string;
  mime_type: string;
  file_size: number;
  checksum_sha256: string;
  version: number;
  status: "active" | "archived";
  extraction_status: "pending" | "completed" | "failed";
  extraction_error: string | null;
  page_count: number;
  extracted_char_count: number;
  uploaded_by: string;
  uploader: UserOption;
  created_at: string;
  updated_at: string;
};

export type BRSDocumentDetail = BRSDocument & { contents: DocumentContent[] };
