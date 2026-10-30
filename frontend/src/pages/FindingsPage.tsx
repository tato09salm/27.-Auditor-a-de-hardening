import { keepPreviousData, useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { Bug, ChevronRight, Search, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Badge,
  EmptyState,
  ErrorState,
  FindingStatusBadge,
  PageHeader,
  Pagination,
  SearchField,
  SeverityBadge,
  TableSkeleton,
} from "../components/ui";
import { findingsApi, serversApi } from "../lib/api";
import { dateTime, shortDate } from "../lib/format";
import { useDebouncedValue } from "../lib/hooks";

const statusOptions = [
  ["", "Todos los estados"],
  ["detected", "Detectado"],
  ["in_review", "En revisión"],
  ["correction_planned", "Corrección planificada"],
  ["fixed_pending_validation", "Pendiente de validación"],
  ["risk_accepted", "Riesgo aceptado"],
  ["resolved", "Resuelto"],
  ["false_positive", "Falso positivo"],
] as const;

export function FindingsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("detected");
  const [serverId, setServerId] = useState("");
  const [page, setPage] = useState(1);
  const [includeClosed, setIncludeClosed] = useState(false);

  const serversQuery = useQuery({
    queryKey: ["servers", "findings-filter"],
    queryFn: () => serversApi.list({ page_size: 200 }),
  });
  const query = useQuery({
    queryKey: ["findings", "list", debouncedSearch, severity, status, serverId, page, includeClosed],
    queryFn: () =>
      findingsApi.list({
        search: debouncedSearch || undefined,
        severity: severity || undefined,
        status: status || undefined,
        server_id: serverId || undefined,
        include_closed: includeClosed || undefined,
        page,
        page_size: 20,
      }),
    placeholderData: keepPreviousData,
  });

  function resetPage() {
    setPage(1);
  }

  return (
    <>
      <PageHeader
        kicker="Ciclo de vida"
        title="Hallazgos"
        description="Incumplimientos persistentes con responsable, severidad y evidencia. El cierre requiere una comprobación posterior o una justificación autorizada."
      />

      <div className="card mb-5 p-3">
        <div className="grid gap-2.5 lg:grid-cols-[1.4fr_repeat(3,minmax(0,0.7fr))_auto]">
          <SearchField
            value={search}
            onChange={(value) => {
              setSearch(value);
              resetPage();
            }}
            placeholder="Buscar hallazgo…"
          />
          <select className="select py-2 text-xs" value={severity} onChange={(event) => { setSeverity(event.target.value); resetPage(); }} aria-label="Severidad">
            <option value="">Todas las severidades</option>
            <option value="critical">Crítica</option>
            <option value="high">Alta</option>
            <option value="medium">Media</option>
            <option value="low">Baja</option>
            <option value="info">Informativa</option>
          </select>
          <select className="select py-2 text-xs" value={status} onChange={(event) => { setStatus(event.target.value); resetPage(); }} aria-label="Estado">
            {statusOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <select className="select py-2 text-xs" value={serverId} onChange={(event) => { setServerId(event.target.value); resetPage(); }} aria-label="Servidor">
            <option value="">Todos los servidores</option>
            {(serversQuery.data?.items ?? []).map((server) => <option key={server.id} value={server.id}>{server.name}</option>)}
          </select>
          <label className="flex items-center gap-2 whitespace-nowrap px-1 text-[11px] font-medium text-slate-500">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-accent-600"
              checked={includeClosed}
              onChange={(event) => {
                setIncludeClosed(event.target.checked);
                resetPage();
              }}
            />
            Incluir cerrados
          </label>
        </div>
      </div>

      {query.isLoading ? (
        <TableSkeleton rows={7} cols={6} />
      ) : query.isError ? (
        <ErrorState message="No se pudieron consultar los hallazgos." onRetry={() => void query.refetch()} />
      ) : query.data?.items.length ? (
        <div className="table-shell">
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <p className="text-xs font-semibold text-slate-500">{query.data.total} hallazgo(s)</p>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
              <ShieldAlert className="h-3.5 w-3.5" />
              Prioridad calculada por severidad
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table min-w-[1000px]">
              <thead>
                <tr>
                  <th>Hallazgo</th>
                  <th>Servidor</th>
                  <th>Severidad</th>
                  <th>Estado</th>
                  <th>Responsable</th>
                  <th>Ocurrencias</th>
                  <th>Vence</th>
                  <th>Última detección</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((finding) => (
                  <tr key={finding.id} className="clickable" onClick={() => navigate(`/findings/${finding.id}`)}>
                    <td>
                      <div className="flex items-start gap-2">
                        <span className={clsx("mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg",
                          finding.severity === "critical" || finding.severity === "high"
                            ? "bg-red-50 text-red-600"
                            : "bg-amber-50 text-amber-600",
                        )}>
                          <Bug className="h-3.5 w-3.5" />
                        </span>
                        <div className="min-w-0">
                          <p className="max-w-[320px] truncate text-xs font-semibold text-ink-900">{finding.title}</p>
                          <div className="mt-0.5 flex items-center gap-2">
                            <span className="font-mono text-[10px] text-slate-400">{finding.cis_reference ?? finding.control_code}</span>
                            {finding.recommendation_count > 0 && (
                              <Badge tone={finding.latest_recommendation_status === "approved" ? "success" : "info"}>
                                {finding.latest_recommendation_status === "approved" ? "Con plan aprobado" : "Con propuesta"}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="max-w-[150px] truncate text-xs">{finding.server_name}</td>
                    <td><SeverityBadge severity={finding.severity} /></td>
                    <td><FindingStatusBadge status={finding.status} /></td>
                    <td className="text-xs">{finding.owner_name ?? <span className="text-slate-400">Sin asignar</span>}</td>
                    <td><span className="text-xs font-semibold tabular-nums">{finding.occurrence_count}</span></td>
                    <td className="whitespace-nowrap text-xs">{finding.due_date ? shortDate(finding.due_date) : "—"}</td>
                    <td className="whitespace-nowrap text-xs text-slate-500">{dateTime(finding.last_seen_at)}</td>
                    <td><ChevronRight className="h-4 w-4 text-slate-300" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={query.data.page} pageSize={query.data.page_size} total={query.data.total} onPageChange={setPage} />
        </div>
      ) : (
        <div className="card">
          <EmptyState
            icon={search ? <Search className="h-5 w-5" /> : <Bug className="h-5 w-5" />}
            title="Sin hallazgos"
            description="No hay incumplimientos que coincidan con los filtros seleccionados."
          />
        </div>
      )}
    </>
  );
}
