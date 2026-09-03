"use client";

import { ArrowLeftIcon, CheckCircleIcon, CpuChipIcon, PaperAirplaneIcon, SparklesIcon, TrashIcon, UserIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { createQnA, deleteQnA, finalizeQnA, generateQnAAnswer, getAIStatus, getQnA, getRelease, updateQnAAnswers } from "@/services/api";
import type { ReleaseDetail } from "@/types/phase6";
import type { AIStatus, QnA } from "@/types/phase7";

type Draft = { supervisor: string; pjk: string; final: string };

function draftOf(item: QnA): Draft {
  return { supervisor: item.supervisor_answer || "", pjk: item.pjk_answer || "", final: item.final_answer || "" };
}

export default function QnAPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthUser();
  const [release, setRelease] = useState<ReleaseDetail | null>(null);
  const [items, setItems] = useState<QnA[]>([]);
  const [ai, setAI] = useState<AIStatus | null>(null);
  const [guestId, setGuestId] = useState("");
  const [question, setQuestion] = useState("");
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = getToken(); if (!token) return;
    Promise.all([getRelease(token, id), getQnA(token, id), getAIStatus(token)]).then(([releaseData, qnaData, aiData]) => {
      setRelease(releaseData); setItems(qnaData); setAI(aiData);
      setDrafts(Object.fromEntries(qnaData.map((item) => [item.id, draftOf(item)])));
    }).catch((err) => setError(err.message));
  }, [id]);

  const active = release?.status === "ongoing";
  const manager = user?.user_level === "admin" || user?.user_level === "humas";
  const canSupervisor = user?.user_level === "admin" || user?.user_level === "supervisor";
  const canPjk = user?.user_level === "admin" || user?.user_level === "pjk";
  const canFinalize = manager || canSupervisor || canPjk;

  function replace(updated: QnA) {
    setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
    setDrafts((current) => ({ ...current, [updated.id]: draftOf(updated) }));
  }
  function setDraft(itemId: string, field: keyof Draft, value: string) {
    setDrafts((current) => ({ ...current, [itemId]: { ...(current[itemId] || { supervisor: "", pjk: "", final: "" }), [field]: value } }));
  }
  async function runAction(name: string, request: (token: string) => Promise<QnA>, success: string) {
    const token = getToken(); if (!token) return;
    setBusy(name); setError(""); setMessage("");
    try { replace(await request(token)); setMessage(success); }
    catch (err) { setError(err instanceof Error ? err.message : "Aksi Q&A gagal."); }
    finally { setBusy(""); }
  }
  async function addQuestion(event: FormEvent) {
    event.preventDefault(); const token = getToken(); if (!token) return;
    setBusy("create"); setError("");
    try { const created = await createQnA(token, id, guestId || null, question); setItems((current) => [...current, created]); setDrafts((current) => ({ ...current, [created.id]: draftOf(created) })); setQuestion(""); setGuestId(""); setMessage("Pertanyaan berhasil dicatat."); }
    catch (err) { setError(err instanceof Error ? err.message : "Pertanyaan gagal dicatat."); }
    finally { setBusy(""); }
  }
  async function remove(item: QnA) {
    if (!window.confirm("Hapus pertanyaan ini?")) return;
    const token = getToken(); if (!token) return;
    try { await deleteQnA(token, item.id); setItems((current) => current.filter((entry) => entry.id !== item.id)); setMessage("Pertanyaan dihapus."); }
    catch (err) { setError(err instanceof Error ? err.message : "Pertanyaan gagal dihapus."); }
  }

  return <AppShell title="Q&A Session"><div className="p-6 lg:p-10">
    <Link href={`/releases/${id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke detail rilis</Link>
    <div className="mt-6 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 7</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Q&A Session</h1><p className="mt-2 text-slate-500">{release?.judul_rilis || "Memuat kegiatan..."}</p></div><span className={`w-fit rounded-full px-4 py-2 text-xs font-bold ${active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{active ? "SESI AKTIF" : "MODE BACA"}</span></div>
    {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}{message && <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{message}</p>}
    <div className={`mt-5 flex items-start gap-3 rounded-xl p-4 text-sm ${ai?.enabled ? "bg-cyan-50 text-cyan-800" : "bg-amber-50 text-amber-800"}`}><CpuChipIcon className="h-6 w-6 shrink-0" /><div><p className="font-semibold">{ai?.enabled ? `AI aktif — ${ai.model}` : "AI belum dikonfigurasi"}</p><p className="mt-1 leading-6">{ai?.enabled ? "Jawaban AI hanya menggunakan data, analisis, fenomena, dan dokumen resmi dalam kegiatan ini." : "Q&A manual tetap dapat digunakan. Isi OPENAI_API_KEY pada .env dan restart backend untuk mengaktifkan saran AI."}</p></div></div>

    {manager && active && <form onSubmit={addQuestion} className="mt-6 rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-bold text-slate-800">Catat Pertanyaan</h2><div className="mt-4 grid gap-4 lg:grid-cols-[0.7fr_1.5fr_auto]"><select value={guestId} onChange={(e) => setGuestId(e.target.value)} className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-cyan-500"><option value="">Penanya tidak tercatat</option>{release?.guests.map((guest) => <option key={guest.id} value={guest.id}>{guest.nama} — {guest.instansi}</option>)}</select><textarea required value={question} onChange={(e) => setQuestion(e.target.value)} rows={2} placeholder="Masukkan pertanyaan peserta..." className="rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-cyan-500" /><button disabled={busy === "create"} className="inline-flex h-fit items-center justify-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 text-sm font-semibold text-white"><PaperAirplaneIcon className="h-5 w-5" />Simpan</button></div></form>}

    <div className="mt-6 space-y-6">{items.map((item, index) => {
      const draft = drafts[item.id] || draftOf(item);
      return <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div className="flex gap-3"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#102a43] text-sm font-bold text-white">{index + 1}</div><div><p className="text-xs font-semibold uppercase text-cyan-700">{item.guest ? `${item.guest.nama} — ${item.guest.instansi}` : "Penanya tidak tercatat"}</p><h2 className="mt-2 text-lg font-bold leading-7 text-slate-800">{item.question}</h2></div></div>{manager && active && <button onClick={() => remove(item)} title="Hapus" className="rounded-lg bg-red-50 p-2 text-red-600"><TrashIcon className="h-4 w-4" /></button>}</div>

        <section className="mt-5 rounded-xl border border-violet-100 bg-violet-50 p-4"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div className="flex items-center gap-2"><SparklesIcon className="h-5 w-5 text-violet-700" /><p className="font-bold text-violet-900">AI Suggested Answer</p></div>{active && canFinalize && <button disabled={!ai?.enabled || Boolean(busy)} onClick={() => runAction(`ai-${item.id}`, (token) => generateQnAAnswer(token, item.id), "Saran jawaban AI berhasil dibuat.")} className="rounded-lg bg-violet-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-40">{busy === `ai-${item.id}` ? "Menyusun..." : item.ai_answer ? "Generate Ulang" : "Jawab dengan AI"}</button>}</div><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-violet-900">{item.ai_answer || "Belum ada saran AI."}</p>{item.ai_sources.length > 0 && <details className="mt-3 text-xs text-violet-700"><summary className="cursor-pointer font-semibold">Lihat {item.ai_sources.length} sumber resmi</summary><ul className="mt-2 list-disc space-y-1 pl-5">{item.ai_sources.map((source) => <li key={source}>{source}</li>)}</ul></details>}{item.ai_answer && active && canFinalize && <button onClick={() => setDraft(item.id, "final", item.ai_answer || "")} className="mt-3 text-xs font-bold text-violet-700">Gunakan sebagai jawaban final</button>}</section>

        <div className="mt-4 grid gap-4 lg:grid-cols-2"><section className="rounded-xl bg-cyan-50 p-4"><p className="font-bold text-cyan-900">Jawaban Supervisor</p>{canSupervisor && active ? <><textarea value={draft.supervisor} onChange={(e) => setDraft(item.id, "supervisor", e.target.value)} rows={4} className="mt-3 w-full rounded-lg border border-cyan-200 bg-white p-3 text-sm outline-none" /><button disabled={Boolean(busy)} onClick={() => runAction(`supervisor-${item.id}`, (token) => updateQnAAnswers(token, item.id, { supervisor_answer: draft.supervisor || null }), "Jawaban Supervisor disimpan.")} className="mt-2 rounded-lg bg-cyan-700 px-3 py-2 text-xs font-semibold text-white">Simpan Jawaban</button></> : <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-cyan-900">{item.supervisor_answer || "Belum diisi."}</p>}{item.supervisor_answer && active && canFinalize && <button onClick={() => setDraft(item.id, "final", item.supervisor_answer || "")} className="mt-3 text-xs font-bold text-cyan-700">Gunakan sebagai jawaban final</button>}</section><section className="rounded-xl bg-emerald-50 p-4"><p className="font-bold text-emerald-900">Jawaban PJK</p>{canPjk && active ? <><textarea value={draft.pjk} onChange={(e) => setDraft(item.id, "pjk", e.target.value)} rows={4} className="mt-3 w-full rounded-lg border border-emerald-200 bg-white p-3 text-sm outline-none" /><button disabled={Boolean(busy)} onClick={() => runAction(`pjk-${item.id}`, (token) => updateQnAAnswers(token, item.id, { pjk_answer: draft.pjk || null }), "Jawaban PJK disimpan.")} className="mt-2 rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white">Simpan Jawaban</button></> : <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-emerald-900">{item.pjk_answer || "Belum diisi."}</p>}{item.pjk_answer && active && canFinalize && <button onClick={() => setDraft(item.id, "final", item.pjk_answer || "")} className="mt-3 text-xs font-bold text-emerald-700">Gunakan sebagai jawaban final</button>}</section></div>

        <section className={`mt-4 rounded-xl border p-4 ${item.final_answer ? "border-emerald-300 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}><div className="flex items-center gap-2"><CheckCircleIcon className="h-5 w-5" /><p className="font-bold text-slate-800">Final Answer — keputusan manusia</p></div>{canFinalize && active ? <><textarea value={draft.final} onChange={(e) => setDraft(item.id, "final", e.target.value)} rows={4} placeholder="Pilih salah satu jawaban di atas atau tulis jawaban final..." className="mt-3 w-full rounded-lg border border-slate-200 bg-white p-3 text-sm outline-none" /><button disabled={!draft.final.trim() || Boolean(busy)} onClick={() => runAction(`final-${item.id}`, (token) => finalizeQnA(token, item.id, draft.final), "Jawaban final berhasil ditetapkan.")} className="mt-2 rounded-lg bg-[#102a43] px-4 py-2 text-xs font-semibold text-white disabled:opacity-40">Tetapkan Jawaban Final</button></> : <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-800">{item.final_answer || "Jawaban final belum ditetapkan."}</p>}{item.finalizer && <p className="mt-3 flex items-center gap-1 text-xs text-emerald-700"><UserIcon className="h-4 w-4" />Ditetapkan oleh {item.finalizer.nama}</p>}</section>
      </article>;
    })}{!items.length && <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-400">Belum ada pertanyaan pada sesi ini.</div>}</div>
  </div></AppShell>;
}

