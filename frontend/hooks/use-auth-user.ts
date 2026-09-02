"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearToken, getToken } from "@/lib/auth";
import { getCurrentUser } from "@/services/api";
import type { User } from "@/types/auth";

export function useAuthUser() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) { router.replace("/login"); return; }
    getCurrentUser(token).then(setUser).catch(() => {
      clearToken(); router.replace("/login");
    }).finally(() => setLoading(false));
  }, [router]);

  function logout() { clearToken(); router.replace("/login"); }
  return { user, loading, logout };
}
