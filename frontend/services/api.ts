import type { TokenResponse, User } from "@/types/auth";
import type { BRS, BRSData, BRSDataForm, BRSForm, DashboardSummary, Indicator, UserOption } from "@/types/phase2";
import type { BRSDocument, BRSDocumentDetail, DocumentType } from "@/types/phase3";
import type { CheckResult, CheckRun, CheckRunDetail, ReviewAction } from "@/types/phase4";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? "Terjadi kesalahan pada layanan STATCHECK.";
  } catch {
    return "Layanan STATCHECK tidak dapat dihubungi.";
  }
}

async function authorizedFetch<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body && !isFormData ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await parseError(response));
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function login(nik: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nik, password }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function getCurrentUser(token: string): Promise<User> {
  const response = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export const getUserOptions = (token: string) => authorizedFetch<UserOption[]>("/users/options", token);
export const getDashboardSummary = (token: string) => authorizedFetch<DashboardSummary>("/dashboard/summary", token);
export const getIndicators = (token: string, activeOnly = false) => authorizedFetch<Indicator[]>(`/indicators?active_only=${activeOnly}`, token);
export const createIndicator = (token: string, payload: Pick<Indicator, "nama_indikator" | "kategori" | "satuan_default" | "fungsi">) => authorizedFetch<Indicator>("/indicators", token, { method: "POST", body: JSON.stringify(payload) });
export const updateIndicator = (token: string, id: string, payload: Omit<Indicator, "id" | "created_at" | "updated_at">) => authorizedFetch<Indicator>(`/indicators/${id}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const getBRSList = (token: string, search = "") => authorizedFetch<BRS[]>(`/brs${search ? `?search=${encodeURIComponent(search)}` : ""}`, token);
export const getBRS = (token: string, id: string) => authorizedFetch<BRS>(`/brs/${id}`, token);
export const createBRS = (token: string, payload: BRSForm) => authorizedFetch<BRS>("/brs", token, { method: "POST", body: JSON.stringify(payload) });
export const updateBRS = (token: string, id: string, payload: BRSForm) => authorizedFetch<BRS>(`/brs/${id}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteBRS = (token: string, id: string) => authorizedFetch<void>(`/brs/${id}`, token, { method: "DELETE" });
export const getBRSData = (token: string, brsId: string) => authorizedFetch<BRSData[]>(`/brs/${brsId}/data`, token);
export const createBRSData = (token: string, brsId: string, payload: BRSDataForm) => authorizedFetch<BRSData>(`/brs/${brsId}/data`, token, { method: "POST", body: JSON.stringify(payload) });
export const updateBRSData = (token: string, brsId: string, dataId: string, payload: BRSDataForm) => authorizedFetch<BRSData>(`/brs/${brsId}/data/${dataId}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteBRSData = (token: string, brsId: string, dataId: string) => authorizedFetch<void>(`/brs/${brsId}/data/${dataId}`, token, { method: "DELETE" });
export const getDocuments = (token: string, brsId: string, includeArchived = false) => authorizedFetch<BRSDocument[]>(`/brs/${brsId}/documents?include_archived=${includeArchived}`, token);
export const getDocument = (token: string, documentId: string) => authorizedFetch<BRSDocumentDetail>(`/documents/${documentId}`, token);
export const uploadDocument = (token: string, brsId: string, documentType: DocumentType, file: File) => {
  const form = new FormData();
  form.append("document_type", documentType);
  form.append("file", file);
  return authorizedFetch<BRSDocumentDetail>(`/brs/${brsId}/documents`, token, { method: "POST", body: form });
};
export const reextractDocument = (token: string, documentId: string) => authorizedFetch<BRSDocumentDetail>(`/documents/${documentId}/reextract`, token, { method: "POST" });
export async function downloadDocument(token: string, document: BRSDocument): Promise<void> {
  const response = await fetch(`${API_URL}/documents/${document.id}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(await parseError(response));
  const url = URL.createObjectURL(await response.blob());
  const link = window.document.createElement("a");
  link.href = url;
  link.download = document.file_name;
  link.click();
  URL.revokeObjectURL(url);
}
export const startCheck = (token: string, brsId: string) => authorizedFetch<CheckRunDetail>(`/brs/${brsId}/check`, token, { method: "POST" });
export const getCheckRuns = (token: string, brsId: string) => authorizedFetch<CheckRun[]>(`/brs/${brsId}/checks`, token);
export const getLatestCheck = (token: string, brsId: string) => authorizedFetch<CheckRunDetail>(`/brs/${brsId}/checks/latest`, token);
export const reviewCheck = (token: string, resultId: string, action: ReviewAction, note: string) => authorizedFetch<CheckResult>(`/checks/${resultId}/review`, token, { method: "POST", body: JSON.stringify({ action, note: note || null }) });
