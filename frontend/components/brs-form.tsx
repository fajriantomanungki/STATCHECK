"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getToken } from "@/lib/auth";
import { useAuthUser } from "@/hooks/use-auth-user";
import { createBRS, getUserOptions, updateBRS } from "@/services/api";
import type { BRSForm as BRSFormType, UserOption } from "@/types/phase2";

const emptyForm: BRSFormType = { nama_brs: "", waktu_rilis: "", fungsi_pj: "", supervisor_id: null, team_user_ids: [] };

export function BRSForm({ initialValue, brsId }: { initialValue?: BRSFormType; brsId?: string }) {
  const router = useRouter();
  const { user: currentUser } = useAuthUser();
  const [form, setForm] = useState(initialValue ?? emptyForm);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { const token = getToken(); if (token) getUserOptions(token).then(setUsers).catch((err) => setError(err.message)); }, []);
  function toggleMember(userId: string) {
    setForm({ ...form, team_user_ids: form.team_user_ids.includes(userId) ? form.team_user_ids.filter((id) => id !== userId) : [...form.team_user_ids, userId] });
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setSaving(true);
    try {
      const token = getToken();
      if (!token) return;
      const saved = brsId ? await updateBRS(token, brsId, form) : await createBRS(token, form);
      router.push(`/brs/${saved.id}`);
    } catch (err) { setError(err instanceof Error ? err.message : "BRS gagal disimpan."); }
    finally { setSaving(false); }
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:p-8">
      <div className="grid gap-5 md:grid-cols-2">
        <label className="md:col-span-2 block text-sm font-medium text-slate-700">Nama BRS<input value={form.nama_brs} onChange={(e) => setForm({ ...form, nama_brs: e.target.value })} required className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Contoh: Perkembangan Pariwisata Juli 2026" /></label>
        <label className="block text-sm font-medium text-slate-700">Waktu rilis<input type="date" value={form.waktu_rilis} onChange={(e) => setForm({ ...form, waktu_rilis: e.target.value })} required className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" /></label>
        <label className="block text-sm font-medium text-slate-700">Fungsi penanggung jawab<input value={form.fungsi_pj} onChange={(e) => setForm({ ...form, fungsi_pj: e.target.value })} required className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Statistik Distribusi" /></label>
        <label className="md:col-span-2 block text-sm font-medium text-slate-700">Supervisor<select value={form.supervisor_id ?? ""} onChange={(e) => setForm({ ...form, supervisor_id: e.target.value || null })} className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none focus:border-cyan-600"><option value="">Belum ditentukan</option>{users.filter((user) => user.id !== currentUser?.id && ["supervisor", "admin"].includes(user.user_level)).map((user) => <option key={user.id} value={user.id}>{user.nama} — {user.user_level}</option>)}</select><span className="mt-1 block text-xs font-normal text-slate-400">Supervisor dapat ditentukan kemudian selama BRS masih berstatus draft.</span></label>
      </div>

      <fieldset className="mt-7"><legend className="text-sm font-semibold text-slate-700">Tim penyusun</legend><div className="mt-3 grid gap-3 md:grid-cols-2">{users.filter((user) => user.id !== currentUser?.id).map((user) => <label key={user.id} className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"><input type="checkbox" checked={form.team_user_ids.includes(user.id)} onChange={() => toggleMember(user.id)} className="h-4 w-4 accent-cyan-700" /><span><span className="block text-sm font-medium text-slate-700">{user.nama}</span><span className="text-xs text-slate-400">{user.fungsi || user.user_level}</span></span></label>)}{!users.length && <p className="text-sm text-slate-400">Memuat pengguna...</p>}</div></fieldset>
      {error && <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="mt-8 flex justify-end gap-3"><button type="button" onClick={() => router.back()} className="rounded-xl border border-slate-300 px-5 py-3 font-semibold text-slate-600">Batal</button><button disabled={saving} className="rounded-xl bg-[#102a43] px-6 py-3 font-semibold text-white disabled:opacity-50">{saving ? "Menyimpan..." : brsId ? "Simpan Perubahan" : "Simpan BRS"}</button></div>
    </form>
  );
}
