import clsx from "clsx";
import {
  Bug,
  CalendarClock,
  ChevronDown,
  FileText,
  KeyRound,
  Layers3,
  LayoutDashboard,
  LogOut,
  Menu,
  Radar,
  ScrollText,
  Server,
  Settings2,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { initials } from "../lib/format";
import { Logo } from "./Logo";

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  permission?: string;
  end?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const groups: NavGroup[] = [
  {
    label: "Operación",
    items: [
      { to: "/", label: "Dashboard", icon: <LayoutDashboard className="h-[18px] w-[18px]" />, permission: "dashboard:read", end: true },
      { to: "/servers", label: "Servidores", icon: <Server className="h-[18px] w-[18px]" />, permission: "servers:read" },
      { to: "/audits", label: "Auditorías", icon: <Radar className="h-[18px] w-[18px]" />, permission: "audits:read" },
      { to: "/findings", label: "Hallazgos", icon: <Bug className="h-[18px] w-[18px]" />, permission: "findings:read" },
      { to: "/recommendations", label: "Recomendaciones IA", icon: <Sparkles className="h-[18px] w-[18px]" />, permission: "recommendations:read" },
    ],
  },
  {
    label: "Gobierno",
    items: [
      { to: "/profiles", label: "Perfiles CIS", icon: <Layers3 className="h-[18px] w-[18px]" />, permission: "profiles:read" },
      { to: "/schedules", label: "Programación", icon: <CalendarClock className="h-[18px] w-[18px]" />, permission: "schedules:manage" },
      { to: "/reports", label: "Reportes", icon: <FileText className="h-[18px] w-[18px]" />, permission: "reports:read" },
    ],
  },
  {
    label: "Administración",
    items: [
      { to: "/users", label: "Usuarios y roles", icon: <Users className="h-[18px] w-[18px]" />, permission: "users:read" },
      { to: "/audit-log", label: "Bitácora", icon: <ScrollText className="h-[18px] w-[18px]" />, permission: "logs:read" },
      { to: "/settings", label: "Configuración", icon: <Settings2 className="h-[18px] w-[18px]" />, permission: "settings:manage" },
    ],
  },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, hasPermission } = useAuth();
  return (
    <div className="flex h-full flex-col">
      <div className="px-5 pb-5 pt-6">
        <Logo size={40} showWordmark light />
      </div>
      <div className="mx-3 mb-4 rounded-xl border border-white/[0.07] bg-white/[0.03] px-3 py-2.5">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5 text-accent-500" />
          Organización
        </div>
        <p className="mt-1 truncate text-xs font-semibold text-slate-200">
          {user?.organization_name ?? "—"}
        </p>
      </div>
      <nav className="scrollbar-none flex-1 overflow-y-auto px-3 pb-4" aria-label="Navegación principal">
        {groups.map((group) => {
          const items = group.items.filter((item) => !item.permission || hasPermission(item.permission));
          if (!items.length) return null;
          return (
            <div key={group.label} className="mb-5">
              <p className="mb-2 px-3 text-[9px] font-bold uppercase tracking-[0.22em] text-slate-600">
                {group.label}
              </p>
              <div className="space-y-1">
                {items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    onClick={onNavigate}
                    className={({ isActive }) => clsx("nav-link", isActive && "nav-link-active")}
                  >
                    {item.icon}
                    <span className="truncate">{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          );
        })}
      </nav>
      <div className="border-t border-white/[0.07] px-4 py-4">
        <div className="flex items-center gap-2 text-[10px] text-slate-500">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_0_3px_rgba(52,211,153,0.12)]" />
          Evaluación de solo lectura
        </div>
        <p className="mt-2 text-[9px] leading-4 text-slate-600">
          CIS Hardening Auditor v1.0 · Los resultados no son una certificación.
        </p>
      </div>
    </div>
  );
}

export function AppShell() {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setMobileOpen(false);
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const roleLabel = user?.roles.map((role) => role.name).join(" · ") ?? "";

  return (
    <div className="min-h-screen lg:flex">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[264px] flex-col overflow-hidden bg-ink-950 lg:flex">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-[radial-gradient(circle_at_20%_0%,rgba(6,182,212,0.16),transparent_60%)]" />
        <div className="relative flex-1">
          <SidebarContent />
        </div>
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink-950/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="relative flex h-full w-[286px] flex-col overflow-hidden bg-ink-950 shadow-2xl animate-fade-up">
            <button
              className="absolute right-3 top-3 z-10 rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"
              onClick={() => setMobileOpen(false)}
              aria-label="Cerrar menú"
            >
              <X className="h-5 w-5" />
            </button>
            <SidebarContent onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col lg:pl-[264px]">
        <header className="sticky top-0 z-20 border-b border-line/80 bg-white/85 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <button
                className="icon-btn lg:hidden"
                onClick={() => setMobileOpen(true)}
                aria-label="Abrir menú"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div className="hidden items-center gap-2 text-xs text-slate-400 sm:flex">
                <ShieldCheck className="h-4 w-4 text-accent-600" />
                <span className="font-medium">Centro de hardening</span>
                <span className="text-slate-300">/</span>
                <span className="font-semibold text-slate-600">
                  {location.pathname === "/" ? "Dashboard" : "Operación"}
                </span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold text-emerald-700 sm:ml-3">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Sesión protegida
              </div>
            </div>

            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen((open) => !open)}
                className="flex items-center gap-2.5 rounded-xl border border-transparent px-1.5 py-1.5 transition hover:border-line hover:bg-slate-50"
                aria-expanded={menuOpen}
                aria-label="Menú de usuario"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink-900 text-[11px] font-bold text-accent-400">
                  {initials(user?.full_name ?? "?")}
                </span>
                <span className="hidden text-left sm:block">
                  <span className="block max-w-[180px] truncate text-xs font-bold text-ink-900">
                    {user?.full_name}
                  </span>
                  <span className="block max-w-[180px] truncate text-[10px] text-slate-400">{roleLabel}</span>
                </span>
                <ChevronDown className="h-4 w-4 text-slate-400" />
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-full z-30 mt-2 w-64 overflow-hidden rounded-xl border border-line bg-white shadow-lift animate-fade-up">
                  <div className="border-b border-line bg-slate-50/70 px-4 py-3">
                    <p className="truncate text-sm font-semibold text-ink-900">{user?.full_name}</p>
                    <p className="truncate text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <div className="p-1.5">
                    <button
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-xs font-medium text-slate-600 hover:bg-slate-50"
                      onClick={() => {
                        setMenuOpen(false);
                        navigate("/change-password");
                      }}
                    >
                      <KeyRound className="h-4 w-4" />
                      Cambiar contraseña
                    </button>
                    <button
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-xs font-medium text-red-600 hover:bg-red-50"
                      onClick={() => void logout()}
                    >
                      <LogOut className="h-4 w-4" />
                      Cerrar sesión
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <div key={location.pathname} className="page-enter">
            <Outlet />
          </div>
        </main>
        <footer className="px-4 pb-6 pt-2 text-center text-[10px] text-slate-400 sm:px-6 lg:px-8">
          Los porcentajes de cumplimiento no certifican la seguridad del servidor. Evidencia y limitaciones
          disponibles en cada auditoría.
        </footer>
      </div>
    </div>
  );
}
