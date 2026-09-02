import { AppShell } from "@/components/app-shell";
import { BRSForm } from "@/components/brs-form";

export default function NewBRSPage() {
  return <AppShell title="Registrasi BRS"><div className="mx-auto max-w-5xl p-6 lg:p-10"><div className="mb-7"><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 2</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Registrasi BRS</h1><p className="mt-2 text-slate-500">Daftarkan identitas, jadwal rilis, supervisor, dan tim penyusun.</p></div><BRSForm /></div></AppShell>;
}
