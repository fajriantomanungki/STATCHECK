import type { TokenResponse, User, UserForm } from "@/types/auth";
import type { BRS, BRSData, BRSDataForm, BRSForm, DashboardSummary, Indicator, PresentationIndicator, UserOption } from "@/types/phase2";
import type { BRSDocument, BRSDocumentDetail, DocumentType } from "@/types/phase3";
import type { CheckResult, CheckRun, CheckRunDetail, ReviewAction } from "@/types/phase4";
import type { ApprovalWorkflow } from "@/types/phase5";
import type { Guest, GuestForm, Release, ReleaseBRS, ReleaseDetail, ReleaseForm } from "@/types/phase6";
import type { AIStatus, Minutes, MinutesForm, QnA } from "@/types/phase7";

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
export const getUsers = (token: string) => authorizedFetch<User[]>("/users", token);
export const createUser = (token: string, payload: Omit<UserForm, "is_active"> & { password: string }) => authorizedFetch<User>("/users", token, { method: "POST", body: JSON.stringify(payload) });
export const updateUser = (token: string, id: string, payload: UserForm) => authorizedFetch<User>(`/users/${id}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteUser = (token: string, id: string) => authorizedFetch<void>(`/users/${id}`, token, { method: "DELETE" });
export const getDashboardSummary = (token: string) => authorizedFetch<DashboardSummary>("/dashboard/summary", token);
export const getIndicators = (token: string, activeOnly = false) => authorizedFetch<Indicator[]>(`/indicators?active_only=${activeOnly}`, token);
export const createIndicator = (token: string, payload: Pick<Indicator, "nama_indikator" | "kategori" | "satuan_default" | "fungsi">) => authorizedFetch<Indicator>("/indicators", token, { method: "POST", body: JSON.stringify(payload) });
export const updateIndicator = (token: string, id: string, payload: Omit<Indicator, "id" | "created_at" | "updated_at">) => authorizedFetch<Indicator>(`/indicators/${id}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteIndicator = (token: string, id: string) => authorizedFetch<void>(`/indicators/${id}`, token, { method: "DELETE" });
export const getBRSList = (token: string, search = "") => authorizedFetch<BRS[]>(`/brs${search ? `?search=${encodeURIComponent(search)}` : ""}`, token);
export const getBRS = (token: string, id: string) => authorizedFetch<BRS>(`/brs/${id}`, token);
export const createBRS = (token: string, payload: BRSForm) => authorizedFetch<BRS>("/brs", token, { method: "POST", body: JSON.stringify(payload) });
export const updateBRS = (token: string, id: string, payload: BRSForm) => authorizedFetch<BRS>(`/brs/${id}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteBRS = (token: string, id: string) => authorizedFetch<void>(`/brs/${id}`, token, { method: "DELETE" });
export const getBRSData = (token: string, brsId: string) => authorizedFetch<BRSData[]>(`/brs/${brsId}/data`, token);
export const createBRSData = (token: string, brsId: string, payload: BRSDataForm) => authorizedFetch<BRSData>(`/brs/${brsId}/data`, token, { method: "POST", body: JSON.stringify(payload) });
export const updateBRSData = (token: string, brsId: string, dataId: string, payload: BRSDataForm) => authorizedFetch<BRSData>(`/brs/${brsId}/data/${dataId}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteBRSData = (token: string, brsId: string, dataId: string) => authorizedFetch<void>(`/brs/${brsId}/data/${dataId}`, token, { method: "DELETE" });
export const getPresentationIndicators = (token: string, brsId: string) => authorizedFetch<PresentationIndicator[]>(`/brs/${brsId}/presentation-indicators`, token);
export const refreshPresentationIndicators = (token: string, brsId: string) => authorizedFetch<PresentationIndicator[]>(`/brs/${brsId}/presentation-indicators/refresh`, token, { method: "POST" });
export const updatePresentationIndicator = (token: string, brsId: string, itemId: string, payload: { analysis: string | null; phenomenon: string | null }) => authorizedFetch<PresentationIndicator>(`/brs/${brsId}/presentation-indicators/${itemId}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deletePresentationIndicator = (token: string, brsId: string, itemId: string) => authorizedFetch<void>(`/brs/${brsId}/presentation-indicators/${itemId}`, token, { method: "DELETE" });
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

const approvalAction = (token: string, brsId: string, path: string, note?: string) =>
  authorizedFetch<ApprovalWorkflow>(`/brs/${brsId}/${path}`, token, {
    method: "POST",
    ...(path.endsWith("start-review") ? {} : { body: JSON.stringify({ note: note?.trim() || null }) }),
  });

export const getApprovalWorkflow = (token: string, brsId: string) => authorizedFetch<ApprovalWorkflow>(`/brs/${brsId}/approval`, token);
export const submitSupervisor = (token: string, brsId: string, note?: string) => approvalAction(token, brsId, "submit-supervisor", note);
export const startSupervisorReview = (token: string, brsId: string) => approvalAction(token, brsId, "supervisor/start-review");
export const supervisorApprove = (token: string, brsId: string, note?: string) => approvalAction(token, brsId, "supervisor/approve", note);
export const supervisorRevision = (token: string, brsId: string, note: string) => approvalAction(token, brsId, "supervisor/revision", note);
export const submitKaBps = (token: string, brsId: string, note?: string) => approvalAction(token, brsId, "submit-ka-bps", note);
export const kaBpsApprove = (token: string, brsId: string, note?: string) => approvalAction(token, brsId, "ka-bps/approve", note);
export const kaBpsRevision = (token: string, brsId: string, note: string) => approvalAction(token, brsId, "ka-bps/revision", note);

export const getReleases = (token: string) => authorizedFetch<Release[]>("/releases", token);
export const getRelease = (token: string, id: string) => authorizedFetch<ReleaseDetail>(`/releases/${id}`, token);
export const getEligibleBRS = (token: string, date: string) => authorizedFetch<ReleaseBRS[]>(`/releases/eligible-brs?tanggal_rilis=${date}`, token);
export const createRelease = (token: string, payload: ReleaseForm) => authorizedFetch<ReleaseDetail>("/releases", token, { method: "POST", body: JSON.stringify(payload) });
export const updateRelease = (token: string, id: string, payload: Omit<ReleaseForm, "brs_ids">) => authorizedFetch<ReleaseDetail>(`/releases/${id}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteRelease = (token: string, id: string) => authorizedFetch<void>(`/releases/${id}`, token, { method: "DELETE" });
export const addReleaseBRS = (token: string, id: string, brsId: string) => authorizedFetch<ReleaseDetail>(`/releases/${id}/brs`, token, { method: "POST", body: JSON.stringify({ brs_id: brsId }) });
export const removeReleaseBRS = (token: string, id: string, brsId: string) => authorizedFetch<ReleaseDetail>(`/releases/${id}/brs/${brsId}`, token, { method: "DELETE" });
export const startRelease = (token: string, id: string) => authorizedFetch<ReleaseDetail>(`/releases/${id}/start`, token, { method: "POST" });
export const completeRelease = (token: string, id: string) => authorizedFetch<ReleaseDetail>(`/releases/${id}/complete`, token, { method: "POST" });
export const getGuests = (token: string, id: string) => authorizedFetch<Guest[]>(`/releases/${id}/guests`, token);
export const createGuest = (token: string, id: string, payload: GuestForm) => authorizedFetch<Guest>(`/releases/${id}/guests`, token, { method: "POST", body: JSON.stringify(payload) });
export const updateGuest = (token: string, guestId: string, payload: GuestForm) => authorizedFetch<Guest>(`/releases/guests/${guestId}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const deleteGuest = (token: string, guestId: string) => authorizedFetch<void>(`/releases/guests/${guestId}`, token, { method: "DELETE" });

export const getAIStatus = (token: string) => authorizedFetch<AIStatus>("/ai/status", token);
export const getQnA = (token: string, releaseId: string) => authorizedFetch<QnA[]>(`/releases/${releaseId}/qna`, token);
export const createQnA = (token: string, releaseId: string, guestId: string | null, question: string) => authorizedFetch<QnA>(`/releases/${releaseId}/qna`, token, { method: "POST", body: JSON.stringify({ guest_id: guestId, question }) });
export const generateQnAAnswer = (token: string, qnaId: string) => authorizedFetch<QnA>(`/qna/${qnaId}/generate-answer`, token, { method: "POST" });
export const updateQnAAnswers = (token: string, qnaId: string, payload: { supervisor_answer?: string | null; pjk_answer?: string | null }) => authorizedFetch<QnA>(`/qna/${qnaId}`, token, { method: "PUT", body: JSON.stringify(payload) });
export const finalizeQnA = (token: string, qnaId: string, finalAnswer: string) => authorizedFetch<QnA>(`/qna/${qnaId}/finalize`, token, { method: "POST", body: JSON.stringify({ final_answer: finalAnswer }) });
export const deleteQnA = (token: string, qnaId: string) => authorizedFetch<void>(`/qna/${qnaId}`, token, { method: "DELETE" });
export const getMinutes = (token: string, releaseId: string) => authorizedFetch<Minutes | null>(`/releases/${releaseId}/minutes`, token);
export const updateMinutes = (token: string, releaseId: string, payload: MinutesForm) => authorizedFetch<Minutes>(`/releases/${releaseId}/minutes`, token, { method: "PUT", body: JSON.stringify(payload) });
export const generateMinutes = (token: string, releaseId: string) => authorizedFetch<Minutes>(`/releases/${releaseId}/minutes/generate`, token, { method: "POST" });
export async function downloadMinutes(token: string, releaseId: string, format: "docx" | "pdf"): Promise<void> {
  const response = await fetch(`${API_URL}/releases/${releaseId}/minutes/download?format=${format}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error(await parseError(response));
  const url = URL.createObjectURL(await response.blob());
  const link = window.document.createElement("a");
  link.href = url;
  link.download = `notulen.${format}`;
  link.click();
  URL.revokeObjectURL(url);
}
