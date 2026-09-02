"use client";

import { ArrowRightIcon, CheckBadgeIcon, DocumentMagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { saveToken } from "@/lib/auth";
import { login } from "@/services/api";

export default function LoginPage() {
  const router = useRouter();
  const [nik, setNik] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(nik.trim(), password);
      saveToken(result.access_token);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login gagal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">
      <section className="relative hidden overflow-hidden bg-[#102a43] p-14 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-cyan-400/10" />
        <div className="absolute -bottom-28 left-24 h-96 w-96 rounded-full bg-blue-400/10" />
        <div className="relative">
          <div className="mb-16 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-cyan-400 text-[#102a43]">
              <DocumentMagnifyingGlassIcon className="h-7 w-7" />
            </div>
            <div><p className="text-xl font-bold tracking-wide">STATCHECK</p><p className="text-xs text-slate-300">BPS Provinsi Sulawesi Tengah</p></div>
          </div>
          <h1 className="max-w-xl text-5xl font-semibold leading-tight">Satu sistem untuk memastikan setiap angka siap dipercaya.</h1>
          <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">Pemeriksaan konsistensi data, pengendalian dokumen, dan persetujuan BRS dalam satu alur kerja terintegrasi.</p>
        </div>
        <div className="relative flex gap-8 text-sm text-slate-300">
          <span className="flex items-center gap-2"><CheckBadgeIcon className="h-5 w-5 text-cyan-300" /> Konsisten</span>
          <span className="flex items-center gap-2"><CheckBadgeIcon className="h-5 w-5 text-cyan-300" /> Terkendali</span>
          <span className="flex items-center gap-2"><CheckBadgeIcon className="h-5 w-5 text-cyan-300" /> Siap Rilis</span>
        </div>
      </section>

      <section className="flex items-center justify-center bg-white px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-9 lg:hidden"><p className="text-2xl font-bold text-[#102a43]">STATCHECK</p><p className="text-sm text-slate-500">BPS Provinsi Sulawesi Tengah</p></div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-700">Selamat datang</p>
          <h2 className="mt-3 text-3xl font-bold text-slate-900">Masuk ke STATCHECK</h2>
          <p className="mt-2 text-slate-500">Gunakan akun internal yang telah terdaftar.</p>

          <form className="mt-9 space-y-5" onSubmit={handleSubmit}>
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-700">NIK</span><input className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-cyan-600 focus:ring-4 focus:ring-cyan-100" value={nik} onChange={(e) => setNik(e.target.value)} placeholder="Masukkan NIK" autoComplete="username" required /></label>
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-700">Password</span><input className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-cyan-600 focus:ring-4 focus:ring-cyan-100" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Masukkan password" autoComplete="current-password" minLength={8} required /></label>
            {error && <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
            <button className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#102a43] px-4 py-3.5 font-semibold text-white transition hover:bg-[#183f62] disabled:cursor-not-allowed disabled:opacity-60" disabled={loading}>{loading ? "Memeriksa..." : "Masuk"}<ArrowRightIcon className="h-5 w-5" /></button>
          </form>
          <p className="mt-10 text-center text-xs text-slate-400">© 2026 BPS Provinsi Sulawesi Tengah</p>
        </div>
      </section>
    </main>
  );
}
