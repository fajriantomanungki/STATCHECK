import type { TokenResponse, User } from "@/types/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? "Terjadi kesalahan pada layanan STATCHECK.";
  } catch {
    return "Layanan STATCHECK tidak dapat dihubungi.";
  }
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
