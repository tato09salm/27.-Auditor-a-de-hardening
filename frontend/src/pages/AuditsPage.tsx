import { keepPreviousData, useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { ChevronRight, Play, Radar, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { StartAuditModal } from "../components/StartAuditModal";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  PageHeader,
  Pagination,
  RunStatusBadge,
  ScoreLabel,
  TableSkeleton,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { auditsApi, serversApi } from "../lib/api";
import { dateTime, percent, scoreTone } from "../lib/format";

export function AuditsPage() {
  const { hasPermission } = useAuth();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [serverId, setServerId] = useState("");
  const [startOpen, setStartOpen] = useState(false);

  const serversQuery = useQuery({
    queryKey: ["servers", "audits-filter"],
    queryFn: () => serversApi.list({ page_size: 200 }),
  });
  const query = useQuery({
    queryKey: ["audits", "list", page, status, serverId],
    queryFn: () =>
      auditsApi.list({
        page,
        page_size: 20,
        status: status || undefined,
        server_id: serverId || undefined,
      }),
    placeholderData: keepPreviousData,
    refetchInterval: (q) => {
      const items = q.state.data?.items ?? [];
      return items.some((run) => run.status === "queued" || run.status === "running") ? 3000 : false;
    },
  });

  return (
    <>
      <PageHeader
        kicker="Evidencia y resultados"
        title="Auditorías"
        description="Cada ejecución conserva su perfil, versión del benchmark y evidencia técnica. Los controles no evaluados nunca cuentan como aprobados."
        actions={
          hasPermission("audits:execute") ? (
            <Button icon={<Play className="h-4 w-4" />} onClick={() => setStartOpen(true)}>
              Nueva auditoría
            </Button>
          ) : undefined
        }
      />

      <div className="card mb-5 p-3">
        <div className="grid gap-2.5 sm:grid-cols-3">
          <select
            className="select py-2 text-xs"
            value={serverId}
            onChange={(event) => {
              setServerId(event.target.value);
              setPage(1);
            }}
            aria-label="Servidor"
          >
            <option value="">Todos los servidores</option>
            {(serversQuery.data?.items ?? []).map((server) => (
              <option key={server.id} value={server.id}>{server.name}</option>
            ))}
          </select>
          <select
            className="select py-2 text-xs"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
            aria-label="Estado"
          >
            <option value="">Todos los estados</option>
            <option value="completed">Completadas</option>
            <option value="running">Ejecutando</option>
            <option value="queued">En cola</option>
            <option value="failed">Fallidas</option>
          </select>
          <div className="flex items-center justify-end text-[10px] text-slate-400">
            {(query.data?.items ?? []).some((run) => run.status === "running" || run.status === "queued")
              ? "Actualización automática activa"
              : "Histórico persistente en PostgreSQL"}
          </div>
        </div>
      </div>

      {query.isLoading ? (
        <TableSkeleton rows={7} cols={6} />
      ) : query.isError ? (
        <ErrorState message="No se pudo consultar el histórico." onRetry={() => void query.refetch()} />
      ) : query.data?.items.length ? (
        <div className="table-shell">
          <div className="overflow-x-auto">
            <table className="data-table min-w-[940px]">
              <thead>
                <tr>
                  <th>Servidor</th>
                  <th>Estado</th>
                  <th>Cumplimiento</th>
                  <th>Aprobados / fallos</th>
                  <th>No evaluados</th>
                  <th>Perfil</th>
                  <th>Ejecutada</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((run) => (
                  <tr key={run.id} className="clickable" onClick={() => navigate(`/audits/${run.id}`)}>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-ink-900">{run.server_name}</span>
                        {run.is_simulated && <Badge tone="warning">Simulado</Badge>}
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-400">{run.server_hostname}</p>
                    </td>
                    <td><RunStatusBadge status={run.status} /></td>
                    <td>
                      <span
                        className={clsx(
                          "text-sm font-bold tabular-nums",
                          scoreTone(run.score) === "good" && "text-emerald-600",
                          scoreTone(run.score) === "warn" && "text-amber-600",
                          scoreTone(run.score) === "bad" && "text-red-600",
                          run.score === null && "text-slate-400",
                        )}
                      >
                        {percent(run.score)}
                      </span>
                    </td>
                    <td>
                      <span className="text-emerald-600">{run.passed_count}</span>
                      <span className="mx-1 text-slate-300">/</span>
                      <span className="text-red-600">{run.failed_count}</span>
                    </td>
                    <td>
                      {run.not_evaluated_count ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-600">
                          <ShieldAlert className="h-3.5 w-3.5" /> {run.not_evaluated_count}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">0</span>
                      )}
                    </td>
                    <td>
                      <p className="max-w-[180px] truncate text-xs">{run.profile_name}</p>
                      <p className="text-[10px] text-slate-400">benchmark v{run.benchmark_version}</p>
                    </td>
                    <td className="whitespace-nowrap text-xs text-slate-500">{dateTime(run.created_at)}</td>
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
            icon={<Radar className="h-5 w-5" />}
            title="Sin auditorías registradas"
            description="Ejecute la primera auditoría autorizada para generar evidencia y puntuaciones."
            action={
              hasPermission("audits:execute") ? (
                <Button icon={<Play className="h-4 w-4" />} onClick={() => setStartOpen(true)}>
                  Nueva auditoría
                </Button>
              ) : undefined
            }
          />
        </div>
      )}
      <StartAuditModal open={startOpen} onClose={() => setStartOpen(false)} />
    </>
  );
}
