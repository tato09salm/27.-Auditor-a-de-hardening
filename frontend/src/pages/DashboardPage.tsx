import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import {
  AlertTriangle,
  ArrowUpRight,
  CalendarRange,
  CheckCircle2,
  ChevronRight,
  Filter,
  Play,
  Radar,
  RefreshCcw,
  Server as ServerIcon,
  ShieldAlert,
  Sparkles,
  XCircle,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { StartAuditModal } from "../components/StartAuditModal";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  PageHeader,
  ScoreRing,
  SectionHeader,
  SeverityBadge,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { dashboardApi, profilesApi, serversApi } from "../lib/api";
import {
  dateTime,
  environmentLabel,
  percent,
  relativeTime,
  runStatusLabel,
  shortDate,
} from "../lib/format";
import type { DashboardData } from "../types";

const PERIODS = [
  { value: "30", label: "Últimos 30 días" },
  { value: "90", label: "Últimos 90 días" },
  { value: "180", label: "Últimos 180 días" },
  { value: "365", label: "Último año" },
];

function periodDates(days: string): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(to.getDate() - Number(days));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function metricTone(value: number | null) {
  if (value === null) return "text-slate-400";
  if (value >= 80) return "text-emerald-600";
  if (value >= 60) return "text-amber-600";
  return "text-red-600";
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-line bg-white px-3 py-2 shadow-lift">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-0.5 text-sm font-bold text-ink-900">{percent(payload[0]?.value)}</p>
    </div>
  );
}

export function DashboardPage() {
  const { hasPermission, user } = useAuth();
  const navigate = useNavigate();
  const [days, setDays] = useState("30");
  const [serverId, setServerId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [environment, setEnvironment] = useState("");
  const [severity, setSeverity] = useState("");
  const [auditOpen, setAuditOpen] = useState(false);
  const dates = useMemo(() => periodDates(days), [days]);

  const dashboardQuery = useQuery({
    queryKey: ["dashboard", days, serverId, profileId, environment, severity],
    queryFn: () =>
      dashboardApi.get({
        date_from: dates.from,
        date_to: dates.to,
        server_id: serverId || undefined,
        profile_id: profileId || undefined,
        environment: environment || undefined,
        severity: severity || undefined,
      }),
  });
  const profilesQuery = useQuery({
    queryKey: ["profiles"],
    queryFn: profilesApi.list,
    enabled: hasPermission("profiles:read"),
  });
  const serversQuery = useQuery({
    queryKey: ["servers", "dashboard-filter"],
    queryFn: () => serversApi.list({ page_size: 200 }),
    enabled: hasPermission("servers:read"),
  });

  const data: DashboardData | undefined = dashboardQuery.data;
  const summary = data?.summary;
  const activeFilters = Boolean(serverId || profileId || environment || severity);

  return (
    <>
      <PageHeader
        kicker="Postura de seguridad"
        title="Dashboard"
        description={
          <>
            Visión consolidada de cumplimiento, hallazgos y actividad de auditoría de{" "}
            <span className="font-semibold text-slate-700">{user?.organization_name}</span>.
          </>
        }
        actions={
          <>
            <Button
              variant="secondary"
              icon={<RefreshCcw className={clsx("h-4 w-4", dashboardQuery.isFetching && "animate-spin")} />}
              onClick={() => void dashboardQuery.refetch()}
            >
              Actualizar
            </Button>
            {hasPermission("audits:execute") && (
              <Button icon={<Play className="h-4 w-4" />} onClick={() => setAuditOpen(true)}>
                Nueva auditoría
              </Button>
            )}
          </>
        }
      />

      <Card className="mb-5 p-3">
        <div className="flex flex-col gap-2.5 lg:flex-row lg:items-center">
          <div className="flex items-center gap-2 px-1 text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400">
            <Filter className="h-3.5 w-3.5" />
            Filtros
          </div>
          <div className="grid flex-1 gap-2 sm:grid-cols-2 lg:grid-cols-5">
            <select className="select py-2 text-xs" value={days} onChange={(event) => setDays(event.target.value)} aria-label="Periodo">
              {PERIODS.map((period) => (
                <option key={period.value} value={period.value}>
                  {period.label}
                </option>
              ))}
            </select>
            <select className="select py-2 text-xs" value={serverId} onChange={(event) => setServerId(event.target.value)} aria-label="Servidor">
              <option value="">Todos los servidores</option>
              {(serversQuery.data?.items ?? []).map((server) => (
                <option key={server.id} value={server.id}>
                  {server.name}
                </option>
              ))}
            </select>
            <select className="select py-2 text-xs" value={profileId} onChange={(event) => setProfileId(event.target.value)} aria-label="Perfil">
              <option value="">Todos los perfiles</option>
              {(profilesQuery.data ?? []).map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
            <select className="select py-2 text-xs" value={environment} onChange={(event) => setEnvironment(event.target.value)} aria-label="Entorno">
              <option value="">Todos los entornos</option>
              <option value="production">Producción</option>
              <option value="staging">Pruebas</option>
              <option value="development">Desarrollo</option>
            </select>
            <select className="select py-2 text-xs" value={severity} onChange={(event) => setSeverity(event.target.value)} aria-label="Severidad">
              <option value="">Todas las severidades</option>
              <option value="critical">Crítica</option>
              <option value="high">Alta</option>
              <option value="medium">Media</option>
              <option value="low">Baja</option>
            </select>
          </div>
          {activeFilters && (
            <button
              className="px-2 text-[11px] font-semibold text-accent-700 hover:underline"
              onClick={() => {
                setServerId("");
                setProfileId("");
                setEnvironment("");
                setSeverity("");
              }}
            >
              Limpiar
            </button>
          )}
        </div>
      </Card>

      {dashboardQuery.isLoading ? (
        <div className="grid gap-5 lg:grid-cols-12">
          <div className="skeleton h-64 lg:col-span-7" />
          <div className="skeleton h-64 lg:col-span-5" />
          <div className="skeleton h-80 lg:col-span-8" />
          <div className="skeleton h-80 lg:col-span-4" />
        </div>
      ) : dashboardQuery.isError ? (
        <ErrorState
          message="No se pudieron obtener los indicadores desde PostgreSQL."
          onRetry={() => void dashboardQuery.refetch()}
        />
      ) : summary ? (
        <>
          <div className="grid gap-5 lg:grid-cols-12">
            <Card className="relative overflow-hidden p-6 lg:col-span-7">
              <div className="pointer-events-none absolute -right-16 -top-24 h-72 w-72 rounded-full bg-cyan-100/50 blur-2xl" />
              <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="section-kicker">Cumplimiento actual</p>
                  <h2 className="mt-1 text-xl font-bold text-ink-950">Postura de hardening</h2>
                  <p className="mt-1.5 max-w-sm text-xs leading-5 text-slate-500">
                    Última evaluación disponible por servidor en el periodo. La cobertura indica qué
                    porcentaje de controles pudo evaluarse.
                  </p>
                  <div className="mt-5 grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Auditados</p>
                      <p className="mt-1 text-lg font-bold text-emerald-600">{summary.audited_servers}</p>
                      <p className="text-[10px] text-slate-400">servidores</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Cobertura</p>
                      <p className="mt-1 text-lg font-bold text-ink-900">{percent(summary.evaluation_coverage)}</p>
                      <p className="text-[10px] text-slate-400">controles evaluados</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Hallazgos</p>
                      <p className="mt-1 text-lg font-bold text-ink-900">
                        {summary.findings_critical + summary.findings_high + summary.findings_medium + summary.findings_low}
                      </p>
                      <p className="text-[10px] text-slate-400">activos</p>
                    </div>
                  </div>
                </div>
                <ScoreRing score={summary.average_score} size={156} strokeWidth={10} />
              </div>
              <div className="relative mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-line pt-4 text-[11px] text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Score = aprobados / aplicables evaluados
                </span>
                <span>No aplicables y no evaluados se excluyen del denominador.</span>
              </div>
            </Card>

            <div className="grid gap-3 sm:grid-cols-2 lg:col-span-5">
              <Card className="p-4">
                <div className="flex items-start justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-500">
                    <ServerIcon className="h-4 w-4" />
                  </span>
                  <Link to="/servers" className="text-slate-300 hover:text-accent-600" aria-label="Ver servidores">
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                </div>
                <p className="mt-4 text-2xl font-bold tabular-nums text-ink-950">{summary.total_servers}</p>
                <p className="text-xs font-medium text-slate-500">Servidores registrados</p>
                <p className="mt-2 text-[10px] text-slate-400">
                  {summary.audited_servers} auditados · {summary.pending_servers} pendientes
                </p>
              </Card>
              <Card className="p-4">
                <div className="flex items-start justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-50 text-accent-700">
                    <Radar className="h-4 w-4" />
                  </span>
                  <Link to="/audits" className="text-slate-300 hover:text-accent-600" aria-label="Ver auditorías">
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                </div>
                <p className="mt-4 text-2xl font-bold tabular-nums text-ink-950">{summary.audits_in_period}</p>
                <p className="text-xs font-medium text-slate-500">Auditorías en el periodo</p>
                <p className="mt-2 text-[10px] text-slate-400">
                  Última: {summary.last_audit_at ? relativeTime(summary.last_audit_at) : "sin ejecuciones"}
                </p>
              </Card>
              <Card className="p-4">
                <div className="flex items-start justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-50 text-red-600">
                    <ShieldAlert className="h-4 w-4" />
                  </span>
                  <Link to="/findings?severity=critical" className="text-slate-300 hover:text-accent-600" aria-label="Ver hallazgos">
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                </div>
                <p className="mt-4 text-2xl font-bold tabular-nums text-ink-950">
                  {summary.findings_critical + summary.findings_high}
                </p>
                <p className="text-xs font-medium text-slate-500">Hallazgos críticos y altos</p>
                <div className="mt-2 flex gap-2 text-[10px]">
                  <span className="text-red-600">{summary.findings_critical} críticos</span>
                  <span className="text-orange-600">{summary.findings_high} altos</span>
                </div>
              </Card>
              <Card className="p-4">
                <div className="flex items-start justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                    <Sparkles className="h-4 w-4" />
                  </span>
                  <Link to="/recommendations?status=pending_review" className="text-slate-300 hover:text-accent-600" aria-label="Ver recomendaciones">
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                </div>
                <p className="mt-4 text-2xl font-bold tabular-nums text-ink-950">{summary.pending_recommendations}</p>
                <p className="text-xs font-medium text-slate-500">Recomendaciones por revisar</p>
                <p className="mt-2 text-[10px] text-slate-400">Ningún comando se ejecuta automáticamente</p>
              </Card>
            </div>
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-12">
            <Card className="p-5 lg:col-span-8">
              <SectionHeader
                title="Evolución del cumplimiento"
                description="Promedio semanal de auditorías completadas."
                action={
                  data?.trend.length ? (
                    <Badge tone="neutral" dot>
                      {data.trend.length} semanas
                    </Badge>
                  ) : undefined
                }
              />
              <div className="mt-5 h-[260px]">
                {data && data.trend.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.trend} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.28} />
                          <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#eef2f7" strokeDasharray="3 3" vertical={false} />
                      <XAxis
                        dataKey="period"
                        tickFormatter={(value: string) => shortDate(value)}
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tickFormatter={(value: number) => `${value}%`}
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                        width={46}
                      />
                      <Tooltip content={<ChartTooltip />} cursor={{ stroke: "#cbd5e1", strokeDasharray: "3 3" }} />
                      <Area
                        type="monotone"
                        dataKey="average_score"
                        stroke="#0891b2"
                        strokeWidth={2.5}
                        fill="url(#scoreFill)"
                        dot={{ r: 3, fill: "#fff", stroke: "#0891b2", strokeWidth: 2 }}
                        activeDot={{ r: 5 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    icon={<CalendarRange className="h-5 w-5" />}
                    title="Aún no hay tendencia"
                    description="Ejecute auditorías en este periodo para visualizar la evolución del cumplimiento."
                    className="h-full py-6"
                  />
                )}
              </div>
            </Card>

            <Card className="p-5 lg:col-span-4">
              <SectionHeader title="Hallazgos por severidad" description="Incumplimientos activos." />
              <div className="mt-5 space-y-4">
                {[
                  { key: "critical", label: "Crítica", value: summary.findings_critical, color: "bg-red-500" },
                  { key: "high", label: "Alta", value: summary.findings_high, color: "bg-orange-500" },
                  { key: "medium", label: "Media", value: summary.findings_medium, color: "bg-amber-500" },
                  { key: "low", label: "Baja", value: summary.findings_low, color: "bg-blue-500" },
                ].map((item) => {
                  const total =
                    summary.findings_critical +
                    summary.findings_high +
                    summary.findings_medium +
                    summary.findings_low +
                    summary.findings_info;
                  const width = total ? Math.max(4, (item.value / total) * 100) : 0;
                  return (
                    <Link key={item.key} to={`/findings?severity=${item.key}`} className="block group">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-600 group-hover:text-ink-900">{item.label}</span>
                        <span className="font-bold tabular-nums text-ink-900">{item.value}</span>
                      </div>
                      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
                        <div className={`h-full rounded-full ${item.color} transition-all`} style={{ width: `${width}%` }} />
                      </div>
                    </Link>
                  );
                })}
              </div>
              <div className="mt-5 rounded-xl border border-dashed border-line bg-slate-50/60 p-3">
                <p className="text-[10px] leading-4 text-slate-500">
                  Los conteos se actualizan con los hallazgos activos. Un hallazgo resuelto permanece en
                  el histórico del servidor.
                </p>
              </div>
            </Card>
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-12">
            <Card className="overflow-hidden lg:col-span-7">
              <div className="p-5 pb-2">
                <SectionHeader
                  title="Controles que fallan con más frecuencia"
                  description="Frecuencia de incumplimiento en el periodo seleccionado."
                />
              </div>
              {data.top_failures.length ? (
                <div className="divide-y divide-line/70">
                  {data.top_failures.map((failure, index) => (
                    <div key={failure.control_id} className="flex items-center gap-3 px-5 py-3.5">
                      <span className="w-4 text-[11px] font-bold tabular-nums text-slate-300">{String(index + 1).padStart(2, "0")}</span>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="truncate text-xs font-semibold text-ink-900">{failure.title}</p>
                          <Badge tone="neutral">{failure.cis_reference ?? "Interno"}</Badge>
                        </div>
                        <div className="mt-1 flex items-center gap-3">
                          <SeverityBadge severity={failure.severity} />
                          <span className="text-[10px] text-slate-400">
                            {failure.affected_servers} servidor(es)
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold tabular-nums text-ink-900">{failure.failure_count}</p>
                        <p className="text-[9px] uppercase tracking-wider text-slate-400">fallos</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<CheckCircle2 className="h-5 w-5" />}
                  title="Sin fallos registrados"
                  description="No hay controles incumplidos en el periodo y filtros actuales."
                />
              )}
            </Card>

            <Card className="overflow-hidden lg:col-span-5">
              <div className="p-5 pb-2">
                <SectionHeader
                  title="Servidores con mayor riesgo"
                  description="Ordenado por hallazgos críticos, altos y score."
                />
              </div>
              {data.riskiest_servers.length ? (
                <div className="divide-y divide-line/70">
                  {data.riskiest_servers.map((server) => (
                    <button
                      key={server.id}
                      onClick={() => navigate(`/servers/${server.id}`)}
                      className="flex w-full items-center gap-3 px-5 py-3.5 text-left transition hover:bg-slate-50"
                    >
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-ink-900 text-[10px] font-bold text-cyan-300">
                        {server.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-semibold text-ink-900">{server.name}</p>
                        <p className="truncate text-[10px] text-slate-400">
                          {server.hostname} · {environmentLabel[server.environment]}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={clsx("text-sm font-bold tabular-nums", metricTone(server.score))}>
                          {percent(server.score)}
                        </p>
                        <p className="text-[9px] text-red-500">{server.critical_findings + server.high_findings} graves</p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-slate-300" />
                    </button>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<ServerIcon className="h-5 w-5" />}
                  title="Sin servidores evaluados"
                  description="Registre y audite servidores para priorizar riesgos."
                />
              )}
            </Card>
          </div>

          <Card className="mt-5 overflow-hidden">
            <div className="flex items-center justify-between gap-4 p-5 pb-2">
              <SectionHeader title="Actividad reciente" description="Últimas ejecuciones registradas." />
              <Link to="/audits" className="text-[11px] font-semibold text-accent-700 hover:underline">
                Ver todas
              </Link>
            </div>
            {data.recent_runs.length ? (
              <div className="overflow-x-auto">
                <table className="data-table min-w-[760px]">
                  <thead>
                    <tr>
                      <th>Servidor</th>
                      <th>Estado</th>
                      <th>Cumplimiento</th>
                      <th>Incumplidos</th>
                      <th>Fecha</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_runs.map((run) => (
                      <tr
                        key={run.id}
                        className="clickable"
                        onClick={() => navigate(`/audits/${run.id}`)}
                      >
                        <td>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-ink-900">{run.server_name}</span>
                            {run.is_simulated && <Badge tone="warning">Simulado</Badge>}
                          </div>
                        </td>
                        <td>
                          <Badge
                            tone={
                              run.status === "completed"
                                ? "success"
                                : run.status === "failed"
                                  ? "danger"
                                  : "info"
                            }
                          >
                            {runStatusLabel[run.status]}
                          </Badge>
                        </td>
                        <td>
                          <span className={clsx("font-bold tabular-nums", metricTone(run.score))}>
                            {percent(run.score)}
                          </span>
                        </td>
                        <td>
                          <span className="inline-flex items-center gap-1 text-xs">
                            <XCircle className="h-3.5 w-3.5 text-red-500" />
                            {run.failed_count}
                          </span>
                        </td>
                        <td className="whitespace-nowrap text-xs text-slate-500">{dateTime(run.created_at)}</td>
                        <td>
                          <ChevronRight className="h-4 w-4 text-slate-300" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                icon={<Radar className="h-5 w-5" />}
                title="Sin auditorías en el periodo"
                description="Inicie una auditoría para comenzar a construir el histórico de seguridad."
                action={
                  hasPermission("audits:execute") ? (
                    <Button icon={<Play className="h-4 w-4" />} onClick={() => setAuditOpen(true)}>
                      Nueva auditoría
                    </Button>
                  ) : undefined
                }
              />
            )}
          </Card>

          {summary.total_servers === 0 && (
            <Card className="mt-5 border-dashed p-6">
              <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50 text-accent-700">
                    <AlertTriangle className="h-5 w-5" />
                  </span>
                  <div>
                    <p className="text-sm font-bold text-ink-900">La plataforma está lista</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Registre el primer servidor y confirme la autorización explícita para auditarlo.
                    </p>
                  </div>
                </div>
                <Link to="/servers">
                  <Button variant="secondary" icon={<ArrowUpRight className="h-4 w-4" />}>
                    Ir a servidores
                  </Button>
                </Link>
              </div>
            </Card>
          )}
        </>
      ) : (
        <ErrorState />
      )}
      <StartAuditModal open={auditOpen} onClose={() => setAuditOpen(false)} />
    </>
  );
}
