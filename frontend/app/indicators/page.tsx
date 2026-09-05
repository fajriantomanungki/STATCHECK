"use client";

import { CheckCircleIcon, CircleStackIcon, PencilSquareIcon, PlusIcon, TrashIcon, XCircleIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { createIndicator, deleteIndicator, getIndicators, updateIndicator } from "@/services/api";
import type { Indicator } from "@/types/phase2";

const initialForm = { nama_indikator: "", kategori: "", satuan_default: "", fungsi: "" };

export default function IndicatorsPage() {
  const [items, setItems] = useState<Indicator[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getToken();
    if (token) setItems(await getIndicators(token));
  }, []);

  useEffect(() => {
    const token = getToken();
    if (token) getIndicators(token).then(setItems).catch((err) => setError(err.message));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setSaving(true);
    try {
      const token = getToken();
      if (!token) return;
      if (editingId) {
        const current = items.find((item) => item.id === editingId);
        await updateIndicator(token, editingId, { ...form, fungsi: form.fungsi || null, is_active: current?.is_active ?? true });
      } else {
        await createIndicator(token, { ...form, fungsi: form.fungsi || null });
      }
      setEditingId(null); setForm(initialForm); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Gagal menyimpan indikator."); }
    finally { setSaving(false); }
  }

  function edit(item: Indicator) {
    setEditingId(item.id);
    setForm({ nama_indikator: item.nama_indikator, kategori: item.kategori, satuan_default: item.satuan_default, fungsi: item.fungsi || "" });
  }

  async function remove(item: Indicator) {
    if (!window.confirm(`Hapus indikator ${item.nama_indikator}?`)) return;
    const token = getToken(); if (!token) return;
    try { await deleteIndicator(token, item.id); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Gagal menghapus indikator."); }
  }

  async function toggle(item: Indicator) {
    const token = getToken();
    if (!token) return;
    try {
      await updateIndicator(token, item.id, {
        nama_indikator: item.nama_indikator, kategori: item.kategori,
        satuan_default: item.satuan_default, fungsi: item.fungsi, is_active: !item.is_active,
      });
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Gagal memperbarui indikator."); }
  }

  return (
    <AppShell title="Master Indikator">
      <div className="p-6 lg:p-10">
        <div className="mb-7"><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 2</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Master Indikator</h1><p className="mt-2 text-slate-500">Daftar indikator yang dapat dipilih pada setiap data BRS.</p></div>

        <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
          <form onSubmit={submit} className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between"><h2 className="flex items-center gap-2 font-bold text-slate-800"><PlusIcon className="h-5 w-5 text-cyan-700" />{editingId ? "Edit Indikator" : "Tambah Indikator"}</h2>{editingId && <button type="button" onClick={() => { setEditingId(null); setForm(initialForm); }} title="Batal edit" className="text-slate-500"><XMarkIcon className="h-5 w-5" /></button>}</div>
            <div className="mt-5 space-y-4">
              <label className="block text-sm font-medium text-slate-700">Nama indikator<input value={form.nama_indikator} onChange={(e) => setForm({ ...form, nama_indikator: e.target.value })} required className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Contoh: Tingkat Penghunian Kamar" /></label>
              <label className="block text-sm font-medium text-slate-700">Kategori<input value={form.kategori} onChange={(e) => setForm({ ...form, kategori: e.target.value })} required className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Contoh: Pariwisata" /></label>
              <label className="block text-sm font-medium text-slate-700">Satuan default<input value={form.satuan_default} onChange={(e) => setForm({ ...form, satuan_default: e.target.value })} required className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="persen" /></label>
              <label className="block text-sm font-medium text-slate-700">Fungsi<input value={form.fungsi} onChange={(e) => setForm({ ...form, fungsi: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Statistik Distribusi" /></label>
            </div>
            {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            <button disabled={saving} className="mt-5 w-full rounded-xl bg-[#102a43] px-4 py-3 font-semibold text-white disabled:opacity-50">{saving ? "Menyimpan..." : editingId ? "Simpan Perubahan" : "Simpan Indikator"}</button>
          </form>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5"><h2 className="flex items-center gap-2 font-bold text-slate-800"><CircleStackIcon className="h-5 w-5 text-cyan-700" />Daftar Indikator</h2><span className="text-sm text-slate-400">{items.length} indikator</span></div>
            <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-6 py-4">Indikator</th><th className="px-6 py-4">Kategori</th><th className="px-6 py-4">Satuan</th><th className="px-6 py-4">Status</th><th className="px-6 py-4"></th></tr></thead><tbody className="divide-y divide-slate-100">
              {items.map((item) => <tr key={item.id}><td className="px-6 py-4 font-medium text-slate-800">{item.nama_indikator}<p className="mt-1 text-xs font-normal text-slate-400">{item.fungsi || "—"}</p></td><td className="px-6 py-4 text-slate-600">{item.kategori}</td><td className="px-6 py-4 text-slate-600">{item.satuan_default}</td><td className="px-6 py-4">{item.is_active ? <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700"><CheckCircleIcon className="h-4 w-4" />Aktif</span> : <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-500"><XCircleIcon className="h-4 w-4" />Nonaktif</span>}</td><td className="px-6 py-4"><div className="flex justify-end gap-2"><button onClick={() => edit(item)} title="Edit" className="rounded-lg bg-cyan-50 p-2 text-cyan-700"><PencilSquareIcon className="h-4 w-4" /></button><button onClick={() => toggle(item)} className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{item.is_active ? "Nonaktifkan" : "Aktifkan"}</button><button onClick={() => remove(item)} title="Hapus" className="rounded-lg bg-red-50 p-2 text-red-600"><TrashIcon className="h-4 w-4" /></button></div></td></tr>)}
              {!items.length && <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-400">Belum ada indikator.</td></tr>}
            </tbody></table></div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
