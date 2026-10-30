import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  FileText,
  Info,
  RotateCcw,
  ShieldAlert,
  Terminal,
  XCircle,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Alert,
  Badge,
  Button,
  Card,
  CheckStatusBadge,
  EmptyState,
  ErrorState,
  EvidenceValue,
  PageLoader,
  RunStatusBadge,
  ScoreRing,
  SectionHeader,
  SeverityBadge,
  TableSkeleton,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { auditsApi } from "../lib/api";
import {
  dateTime,
  percent,
  prettyJson,
  runStatusLabel,
  scoreTone,
  severityLabel,
  statusLabel,
} from "../lib/format";
import type { Check } from "../types";

function CheckRow({ check }: { check: Check }) {
  const [open, setOpen] = useState(false);
  const evidence = check.evidence ?? {};
  const stdout = typeof evidence.stdout === "string" ? evidence.stdout : "";
  const stderr = typeof evidence.stderr === "string" ? evidence.stderr : "";
  return (
    <>
      <tr className="clickable" onClick={() => setOpen((current) => !current)}>
        <td className="w-8">
          {open ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
        </td>
        <td>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] font-bold text-slate-400">{check.control_code}</span>
            <span className="text-xs font-semibold text-ink-900">{check.control_title}</span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-400">
            {check.cis_reference ? `CIS ${check.cis_reference}` : "Control interno"} · {check.category}
          </p>
        </td>
        <td><SeverityBadge severity={check.severity} /></td>
        <td><CheckStatusBadge status={check.status} /></td>
        <td className="max-w-[320px] text-xs text-slate-600">{check.observed_value ?? "—"}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={5} className="!bg-slate-50/70 !px-5 !py-5">
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Resultado observado</p>
                <p className="text-xs leading-6 text-slate-700">{check.observed_value ?? "Sin observación."}</p>
                {check.error_message && (
                  <Alert tone="warning" className="mt-3" title="Error de evaluación">
                    {check.error_message}
                  </Alert>
                )}
                <p className="mb-2 mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Guía de corrección de referencia</p>
                <p className="text-xs leading-6 text-slate-600">{check.remediation_guidance}</p>
                {check.mapping_notes && (
                  <p className="mt-3 rounded-lg border border-line bg-white p-2.5 text-[10px] leading-5 text-slate-500">
                    <span className="font-bold">Mapeo:</span> {check.mapping_notes}
                  </p>
                )}
              </div>
              <div className="space-y-3">
                <div>
                  <p className="mb-2 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                    <Terminal className="h-3.5 w-3.5" /> Evidencia de ejecución
                  </p>
                  {stdout || stderr ? (
                    <EvidenceValue value={stdout || stderr} />
                  ) : (
                    <div className="rounded-xl border border-dashed border-line bg-white p-4 text-xs text-slate-400">
                      Sin salida registrada para este control.
                    </div>
                  )}
                </div>
                {check.command_executed && (
                  <details className="rounded-xl border border-line bg-white p-3">
                    <summary className="cursor-pointer text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Comando ejecutado (solo lectura)
                    </summary>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words font-mono text-[10px] leading-5 text-slate-500">
                      {check.command_executed}
                    </pre>
                  </details>
                )}
                <details className="rounded-xl border border-line bg-white p-3">
                  <summary className="cursor-pointer text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Evidencia estructurada
                  </summary>
                  <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] leading-5 text-slate-500">
                    {prettyJson(evidence)}
                  </pre>
                </details>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export function AuditDetailPage() {
  const { runId = "" } = useParams();
  const { hasPermission } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");

  const query = useQuery({
    queryKey: ["audit", runId],
    queryFn: () => auditsApi.get(runId),
    enabled: Boolean(runId),
    refetchInterval: (q) => {
      const data = q.state.data;
      return data?.status === "queued" || data?.status === "running" ? 2200 : false;
    },
  });

  const checks = useMemo(
    () =>
      (query.data?.checks ?? []).filter(
        (check) =>
          (!statusFilter || check.status === statusFilter) &&
          (!severityFilter || check.severity === severityFilter),
      ),
    [query.data?.checks, statusFilter, severityFilter],
  );

  if (query.isLoading) return <PageLoader label="Cargando resultados de auditoría…" />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Auditoría no disponible"
        message="El registro no existe o pertenece a otra organización."
        onRetry={() => void query.refetch()}
      />
    );
  }
  const run = query.data;
  const inProgress = run.status === "queued" || run.status === "running";
  const coverage = Number((run.summary as { coverage?: number }).coverage ?? 0);
  const limitations = (run.summary as { limitations?: string[] }).limitations ?? [];

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <Link to="/audits" className="inline-flex items-center gap-1 font-medium hover:text-slate-700">
          <ArrowLeft className="h-3.5 w-3.5" /> Auditorías
        </Link>
        <span>/</span>
        <span className="font-mono font-semibold text-slate-600">{run.id.slice(0, 8)}</span>
      </div>

      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink-950 sm:text-3xl">
              {run.server_name ?? "Servidor"}
            </h1>
            <RunStatusBadge status={run.status} />
            {run.is_simulated && <Badge tone="warning">Simulado</Badge>}
          </div>
          <p className="mt-1 text-sm text-slate-500">
            {run.profile_name} · benchmark v{run.benchmark_version} ·{" "}
            {run.triggered_by_name ? `por ${run.triggered_by_name}` : "automatización"} ·{" "}
            {dateTime(run.created_at)}
          </p>
          <div className="mt-2 flex flex-wrap gap-4 text-[11px] text-slate-400">
            <span>Inicio: {dateTime(run.started_at)}</span>
            <span>Fin: {dateTime(run.finished_at)}</span>
            <span className="font-mono">ID {run.id}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {run.server_id && (
            <Button variant="secondary" icon={<ShieldAlert className="h-4 w-4" />} onClick={() => navigate(`/servers/${run.server_id}`)}>
              Ver servidor
            </Button>
          )}
          {hasPermission("reports:generate") && run.status === "completed" && (
            <Button
              variant="secondary"
              icon={<FileText className="h-4 w-4" />}
              onClick={() => navigate(`/reports?run_id=${run.id}&server_id=${run.server_id}`)}
            >
              Generar reporte
            </Button>
          )}
          {hasPermission("audits:execute") && (
            <Button
              icon={<RotateCcw className="h-4 w-4" />}
              onClick={async () => {
                try {
                  const created = await auditsApi.create({
                    server_id: run.server_id,
                    profile_id: run.profile_id,
                  });
                  notify({
                    tone: "success",
                    title: "Auditoría en cola",
                    message: "Se inició una nueva ejecución con el mismo perfil.",
                  });
                  navigate(`/audits/${created.id}`);
                } catch {
                  notify({
                    tone: "error",
                    title: "No se pudo reintentar",
                    message: "Puede existir una auditoría en curso o el servidor no está autorizado.",
                  });
                }
              }}
            >
              Reintentar
            </Button>
          )}
        </div>
      </div>

      {inProgress && (
        <Alert tone="info" className="mb-5" title="Auditoría en ejecución">
          Los controles se están evaluando. Esta página se actualiza automáticamente.
        </Alert>
      )}
      {run.status === "failed" && (
        <Alert tone="danger" className="mb-5" title="La evaluación no se completó">
          {run.error_message ?? "No se obtuvieron resultados utilizables. El score no se calcula."}
        </Alert>
      )}
      {run.is_simulated && (
        <Alert tone="warning" className="mb-5" title="Resultados simulados">
          Esta ejecución usó el conector de pruebas y no contactó infraestructura real.
        </Alert>
      )}

      <div className="grid gap-5 xl:grid-cols-12">
        <Card className="p-5 xl:col-span-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="section-kicker">Cumplimiento</p>
              <p className="mt-1 text-xs text-slate-500">Fórmula transparente</p>
            </div>
            <Badge tone={coverage >= 90 ? "success" : "warning"}>{coverage.toFixed(0)}% cobertura</Badge>
          </div>
          <div className="mt-5 flex justify-center">
            <ScoreRing score={run.score} size={176} strokeWidth={11} />
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3">
            {[
              { label: "Aprobados", value: run.passed_count, icon: <CheckCircle2 className="h-4 w-4 text-emerald-600" /> },
              { label: "Incumplidos", value: run.failed_count, icon: <XCircle className="h-4 w-4 text-red-600" /> },
              { label: "No aplicables", value: run.not_applicable_count, icon: <Info className="h-4 w-4 text-slate-400" /> },
              { label: "No evaluados", value: run.not_evaluated_count, icon: <AlertTriangle className="h-4 w-4 text-amber-500" /> },
            ].map((item) => (
              <div key={item.label} className="rounded-xl border border-line bg-slate-50/60 p-3">
                <div className="flex items-center gap-1.5">{item.icon}<span className="text-[10px] font-semibold text-slate-500">{item.label}</span></div>
                <p className="mt-1.5 text-xl font-bold tabular-nums text-ink-950">{item.value}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-[10px] leading-5 text-slate-400">
            Score = aprobados / (aprobados + incumplidos) × 100. No aplicables y no evaluados se
            excluyen del denominador.
          </p>
        </Card>

        <Card className="p-5 xl:col-span-8">
          <SectionHeader
            title="Resumen de la ejecución"
            description="Indicadores calculados a partir de los controles efectivamente evaluados."
          />
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-line p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Controles del perfil</p>
              <p className="mt-1.5 text-2xl font-bold text-ink-950">{run.total_controls}</p>
            </div>
            <div className="rounded-xl border border-line p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Hallazgos creados</p>
              <p className="mt-1.5 text-2xl font-bold text-ink-950">{run.findings_created}</p>
            </div>
            <div className="rounded-xl border border-line p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Hallazgos resueltos</p>
              <p className="mt-1.5 text-2xl font-bold text-emerald-600">{run.findings_resolved}</p>
            </div>
          </div>
          {Array.isArray((run.summary as { failed_controls?: unknown[] }).failed_controls) &&
            (run.summary as { failed_controls: { title: string; severity: string; code: string }[] }).failed_controls.length > 0 && (
              <div className="mt-5">
                <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">Controles incumplidos</p>
                <div className="flex flex-wrap gap-2">
                  {(run.summary as { failed_controls: { title: string; severity: string; code: string }[] }).failed_controls
                    .slice(0, 8)
                    .map((item) => (
                      <span key={item.code} className="rounded-lg border border-line bg-slate-50 px-2 py-1 text-[10px] font-medium text-slate-600">
                        {item.title}
                      </span>
                    ))}
                </div>
              </div>
            )}
          {limitations.length > 0 && (
            <div className="mt-5 rounded-xl border border-amber-100 bg-amber-50/50 p-3.5">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Limitaciones de la evaluación</p>
              <ul className="mt-2 space-y-1 text-[10px] leading-5 text-amber-800/80">
                {limitations.map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
          )}
        </Card>
      </div>

      <Card className="mt-5 overflow-hidden">
        <div className="flex flex-col gap-3 p-5 pb-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="section-title">Resultados por control</h2>
            <p className="mt-1 text-xs text-slate-500">Haga clic en una fila para revisar la evidencia técnica.</p>
          </div>
          <div className="flex gap-2">
            <select className="select w-auto py-1.5 text-xs" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} aria-label="Estado">
              <option value="">Todos los estados</option>
              <option value="passed">Aprobados</option>
              <option value="failed">Incumplidos</option>
              <option value="not_applicable">No aplica</option>
              <option value="not_evaluated">No evaluados</option>
            </select>
            <select className="select w-auto py-1.5 text-xs" value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)} aria-label="Severidad">
              <option value="">Todas</option>
              <option value="critical">Crítica</option>
              <option value="high">Alta</option>
              <option value="medium">Media</option>
              <option value="low">Baja</option>
            </select>
          </div>
        </div>
        {query.isFetching && inProgress ? (
          <div className="p-5"><TableSkeleton rows={5} cols={5} /></div>
        ) : checks.length ? (
          <div className="overflow-x-auto">
            <table className="data-table min-w-[840px]">
              <thead>
                <tr>
                  <th />
                  <th>Control</th>
                  <th>Severidad</th>
                  <th>Estado</th>
                  <th>Resultado observado</th>
                </tr>
              </thead>
              <tbody>
                {checks.map((check) => <CheckRow key={check.id} check={check} />)}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={<CheckCircle2 className="h-5 w-5" />}
            title="Sin controles para este filtro"
            description="Cambie el estado o la severidad para revisar otros resultados."
          />
        )}
      </Card>
    </>
  );
}
