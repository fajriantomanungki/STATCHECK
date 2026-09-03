"use client";

import { ArrowLeftIcon, PencilSquareIcon, PlusIcon, TrashIcon, UserGroupIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { createGuest, deleteGuest, getRelease, updateGuest } from "@/services/api";
import type { Guest, GuestForm, ReleaseDetail } from "@/types/phase6";

const emptyForm: GuestForm = { nama: "", instansi: "", jabatan: null, nomor_hp: null, email: null };

export default function GuestsPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthUser();
  const [release, setRelease] = useState<ReleaseDetail | null>(null);
  const [form, setForm] = useState<GuestForm>(emptyForm);
  const [editing, setEditing] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const canManage = (user?.user_level === "admin" || user?.user_level === "humas") && release?.status !== "completed";
  useEffect(() => { const token = getToken(); if (token) getRelease(token, id).then(setRelease).catch((err) => setError(err.message)); }, [id]);

  function edit(guest: Guest) { setEditing(guest.id); setForm({ nama: guest.nama, instansi: guest.instansi, jabatan: guest.jabatan, nomor_hp: guest.nomor_hp, email: guest.email }); setMessage(""); }
  function reset() { setEditing(null); setForm(emptyForm); }
  async function submit(event: FormEvent) {
    event.preventDefault(); const token = getToken(); if (!token || !release) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const saved = editing ? await updateGuest(token, editing, form) : await createGuest(token, id, form);
      setRelease({ ...release, guests: editing ? release.guests.map((item) => item.id === saved.id ? saved : item) : [...release.guests, saved], jumlah_tamu: editing ? release.jumlah_tamu : release.jumlah_tamu + 1 });
      setMessage(editing ? "Data peserta berhasil diperbarui." : "Peserta berhasil ditambahkan."); reset();
    } catch (err) { setError(err instanceof Error ? err.message : "Data peserta gagal disimpan."); }
    finally { setBusy(false); }
  }
  async function remove(guest: Guest) {
    if (!window.confirm(`Hapus ${guest.nama} dari daftar peserta?`)) return;
    const token = getToken(); if (!token || !release) return;
    try { await deleteGuest(token, guest.id); setRelease({ ...release, guests: release.guests.filter((item) => item.id !== guest.id), jumlah_tamu: release.jumlah_tamu - 1 }); setMessage("Peserta berhasil dihapus."); }
    catch (err) { setError(err instanceof Error ? err.message : "Peserta gagal dihapus."); }
  }

  return <AppShell title="Daftar Undangan"><div className="p-6 lg:p-10">
    <Link href={`/releases/${id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke detail rilis</Link>
    <div className="mt-6"><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 6</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Daftar Undangan</h1><p className="mt-2 text-slate-500">{release?.judul_rilis || "Memuat kegiatan..."}</p></div>
    {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}{message && <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{message}</p>}
    <div className="mt-7 grid gap-6 xl:grid-cols-[0.8fr_1.4fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-bold text-slate-800">{editing ? "Edit Peserta" : "Tambah Peserta"}</h2>{canManage ? <form onSubmit={submit} className="mt-5 space-y-4"><label className="block text-sm font-semibold text-slate-700">Nama<input required value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label><label className="block text-sm font-semibold text-slate-700">Instansi<input required value={form.instansi} onChange={(e) => setForm({ ...form, instansi: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label><label className="block text-sm font-semibold text-slate-700">Jabatan<input value={form.jabatan || ""} onChange={(e) => setForm({ ...form, jabatan: e.target.value || null })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label><div className="grid gap-4 sm:grid-cols-2"><label className="block text-sm font-semibold text-slate-700">Nomor HP<input value={form.nomor_hp || ""} onChange={(e) => setForm({ ...form, nomor_hp: e.target.value || null })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label><label className="block text-sm font-semibold text-slate-700">Email<input type="email" value={form.email || ""} onChange={(e) => setForm({ ...form, email: e.target.value || null })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label></div><div className="flex gap-2"><button disabled={busy} className="inline-flex items-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 text-sm font-semibold text-white disabled:opacity-40"><PlusIcon className="h-5 w-5" />{busy ? "Menyimpan..." : editing ? "Simpan Perubahan" : "Tambah Peserta"}</button>{editing && <button type="button" onClick={reset} className="rounded-xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-600">Batal</button>}</div></form> : <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">Daftar peserta hanya dapat diubah oleh Humas/Admin sebelum kegiatan selesai.</p>}</section>
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white"><div className="flex items-center gap-3 border-b border-slate-100 p-6"><UserGroupIcon className="h-6 w-6 text-cyan-700" /><div><h2 className="font-bold text-slate-800">Peserta Terdaftar</h2><p className="text-sm text-slate-500">{release?.guests.length || 0} orang</p></div></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-400"><tr><th className="px-5 py-3">Nama</th><th className="px-5 py-3">Instansi</th><th className="px-5 py-3">Kontak</th><th className="px-5 py-3"></th></tr></thead><tbody className="divide-y divide-slate-100">{release?.guests.map((guest) => <tr key={guest.id}><td className="px-5 py-4"><p className="font-semibold text-slate-800">{guest.nama}</p><p className="text-xs text-slate-400">{guest.jabatan || "—"}</p></td><td className="px-5 py-4 text-slate-600">{guest.instansi}</td><td className="px-5 py-4 text-slate-600"><p>{guest.nomor_hp || "—"}</p><p className="text-xs text-slate-400">{guest.email || "—"}</p></td><td className="px-5 py-4"><div className="flex justify-end gap-2">{canManage && <><button onClick={() => edit(guest)} title="Edit" className="rounded-lg bg-cyan-50 p-2 text-cyan-700"><PencilSquareIcon className="h-4 w-4" /></button><button onClick={() => remove(guest)} title="Hapus" className="rounded-lg bg-red-50 p-2 text-red-700"><TrashIcon className="h-4 w-4" /></button></>}</div></td></tr>)}{!release?.guests.length && <tr><td colSpan={4} className="px-5 py-12 text-center text-slate-400">Belum ada peserta yang terdaftar.</td></tr>}</tbody></table></div></section>
    </div>
  </div></AppShell>;
}

