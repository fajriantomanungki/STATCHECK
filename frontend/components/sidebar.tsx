import { ChartBarSquareIcon, DocumentTextIcon, HomeIcon, RocketLaunchIcon } from "@heroicons/react/24/outline";

const items = [
  { name: "Dashboard", icon: HomeIcon, active: true },
  { name: "Berita Resmi Statistik", icon: DocumentTextIcon },
  { name: "Pemeriksaan", icon: ChartBarSquareIcon },
  { name: "Release Center", icon: RocketLaunchIcon },
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-72 shrink-0 bg-[#102a43] px-5 py-7 text-white lg:block">
      <div className="mb-12 px-3"><p className="text-xl font-bold tracking-wide">STATCHECK</p><p className="mt-1 text-xs text-slate-400">Quality before release</p></div>
      <nav className="space-y-2">
        {items.map(({ name, icon: Icon, active }) => (
          <div key={name} className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm ${active ? "bg-cyan-400 font-semibold text-[#102a43]" : "text-slate-300"}`}>
            <Icon className="h-5 w-5" /><span>{name}</span>{!active && <span className="ml-auto text-[10px] uppercase text-slate-500">Segera</span>}
          </div>
        ))}
      </nav>
      <div className="mt-12 rounded-xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-slate-400">Phase 1 aktif<br /><span className="text-slate-200">Foundation & Authentication</span></div>
    </aside>
  );
}
