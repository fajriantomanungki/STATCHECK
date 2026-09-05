"use client";

import { PencilSquareIcon, PlusIcon, TrashIcon, UsersIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { createUser, deleteUser, getUsers, updateUser } from "@/services/api";
import type { User, UserForm } from "@/types/auth";

const emptyForm: UserForm = {
  nama: "", nik: "", user_level: "pjk", fungsi: "", is_active: true, password: "",
};
const roleLabels: Record<UserForm["user_level"], string> = {
  admin: "Administrator", pjk: "PJK", supervisor: "Supervisor", ka_bps: "Kepala BPS", humas: "Humas",
};

export default function UsersPage() {
  const { user } = useAuthUser();
  const [items, setItems] = useState<User[]>([]);
  const [form, setForm] = useState<UserForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const token = getToken();
    if (token) setItems(await getUsers(token));
  }, []);
  useEffect(() => {
    const token = getToken();
    if (token) getUsers(token).then(setItems).catch((err) => setError(err.message));
  }, []);

  function edit(item: User) {
    setEditingId(item.id);
    setForm({
      nama: item.nama, nik: item.nik,
      user_level: item.user_level as UserForm["user_level"],
      fungsi: item.fungsi || "", is_active: item.is_active, password: "",
    });
  }
  function cancel() { setEditingId(null); setForm(emptyForm); setError(""); }

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError("");
    const token = getToken();
    if (!token) return;
    try {
      if (editingId) {
        await updateUser(token, editingId, { ...form, fungsi: form.fungsi || null, password: form.password || null });
      } else {
        if (!form.password) throw new Error("Password awal wajib diisi minimal 8 karakter.");
        await createUser(token, { ...form, fungsi: form.fungsi || null, password: form.password });
      }
      cancel(); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Pengguna gagal disimpan."); }
    finally { setSaving(false); }
  }

  async function remove(item: User) {
    if (!window.confirm(`Hapus pengguna ${item.nama}?`)) return;
    const token = getToken(); if (!token) return;
    try { await deleteUser(token, item.id); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Pengguna gagal dihapus."); }
  }

  if (user && user.user_level !== "admin") {
    return <AppShell title="Kelola User"><div className="p-6 lg:p-10"><p className="rounded-xl bg-amber-50 p-4 text-amber-800">Menu ini hanya tersedia untuk administrator.</p></div></AppShell>;
  }

  return <AppShell title="Kelola User"><div className="p-6 lg:p-10">
    <div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Administrasi</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Kelola User</h1><p className="mt-2 text-slate-500">Tambah, edit, aktifkan, nonaktifkan, atau hapus akun pengguna STATCHECK.</p></div>
    {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
    <div className="mt-7 grid gap-6 xl:grid-cols-[390px_1fr]">
      <form onSubmit={submit} className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between"><h2 className="flex items-center gap-2 font-bold text-slate-800"><PlusIcon className="h-5 w-5 text-cyan-700" />{editingId ? "Edit User" : "Tambah User"}</h2>{editingId && <button type="button" onClick={cancel} className="text-slate-500"><XMarkIcon className="h-5 w-5" /></button>}</div>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium text-slate-700">Nama<input required value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3" /></label>
          <label className="block text-sm font-medium text-slate-700">NIK / username<input required value={form.nik} onChange={(e) => setForm({ ...form, nik: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3" /></label>
          <label className="block text-sm font-medium text-slate-700">Peran<select value={form.user_level} onChange={(e) => setForm({ ...form, user_level: e.target.value as UserForm["user_level"] })} className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3">{Object.entries(roleLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label className="block text-sm font-medium text-slate-700">Fungsi<input value={form.fungsi || ""} onChange={(e) => setForm({ ...form, fungsi: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3" /></label>
          <label className="block text-sm font-medium text-slate-700">{editingId ? "Password baru (opsional)" : "Password awal"}<input type="password" required={!editingId} minLength={8} value={form.password || ""} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3" /></label>
          {editingId && <label className="flex items-center gap-3 text-sm font-medium text-slate-700"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="h-4 w-4" />Akun aktif</label>}
        </div>
        <button disabled={saving} className="mt-5 w-full rounded-xl bg-[#102a43] px-4 py-3 font-semibold text-white disabled:opacity-50">{saving ? "Menyimpan..." : editingId ? "Simpan Perubahan" : "Tambah User"}</button>
      </form>
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-200 px-6 py-5"><h2 className="flex items-center gap-2 font-bold text-slate-800"><UsersIcon className="h-5 w-5 text-cyan-700" />Daftar User</h2><span className="text-sm text-slate-400">{items.length} akun</span></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-5 py-4">User</th><th className="px-5 py-4">Peran</th><th className="px-5 py-4">Status</th><th className="px-5 py-4"></th></tr></thead><tbody className="divide-y divide-slate-100">
        {items.map((item) => <tr key={item.id}><td className="px-5 py-4"><p className="font-semibold text-slate-800">{item.nama}</p><p className="text-xs text-slate-400">{item.nik} • {item.fungsi || "Tanpa fungsi"}</p></td><td className="px-5 py-4 text-slate-600">{roleLabels[item.user_level as UserForm["user_level"]] || item.user_level}</td><td className="px-5 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${item.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{item.is_active ? "Aktif" : "Nonaktif"}</span></td><td className="px-5 py-4"><div className="flex justify-end gap-2"><button onClick={() => edit(item)} title="Edit" className="rounded-lg bg-cyan-50 p-2 text-cyan-700"><PencilSquareIcon className="h-4 w-4" /></button><button onClick={() => remove(item)} title="Hapus" disabled={item.id === user?.id} className="rounded-lg bg-red-50 p-2 text-red-600 disabled:opacity-30"><TrashIcon className="h-4 w-4" /></button></div></td></tr>)}
      </tbody></table></div></div>
    </div>
  </div></AppShell>;
}
