"use client";

import { ChartBarSquareIcon, CircleStackIcon, DocumentTextIcon, HomeIcon, RocketLaunchIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { name: "Dashboard", icon: HomeIcon, href: "/dashboard" },
  { name: "Berita Resmi Statistik", icon: DocumentTextIcon, href: "/brs" },
  { name: "Master Indikator", icon: CircleStackIcon, href: "/indicators" },
  { name: "Pemeriksaan", icon: ChartBarSquareIcon, disabled: true },
  { name: "Release Center", icon: RocketLaunchIcon, disabled: true },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden min-h-screen w-72 shrink-0 bg-[#102a43] px-5 py-7 text-white lg:block">
      <div className="mb-12 px-3"><p className="text-xl font-bold tracking-wide">STATCHECK</p><p className="mt-1 text-xs text-slate-400">Quality before release</p></div>
      <nav className="space-y-2">
        {items.map(({ name, icon: Icon, href, disabled }) => {
          const active = Boolean(href && (pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`))));
          const content = <><Icon className="h-5 w-5" /><span>{name}</span>{disabled && <span className="ml-auto text-[10px] uppercase text-slate-500">Segera</span>}</>;
          const className = `flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition ${active ? "bg-cyan-400 font-semibold text-[#102a43]" : disabled ? "cursor-not-allowed text-slate-500" : "text-slate-300 hover:bg-white/10 hover:text-white"}`;
          return href ? <Link key={name} href={href} className={className}>{content}</Link> : <div key={name} className={className}>{content}</div>;
        })}
      </nav>
      <div className="mt-12 rounded-xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-slate-400">Phase 2 aktif<br /><span className="text-slate-200">BRS & Master Indikator</span></div>
    </aside>
  );
}
