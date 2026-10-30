import { keepPreviousData, useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { ChevronRight, ShieldAlert, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  Badge,
  EmptyState,
  ErrorState,
  PageHeader,
  Pagination,
  RecommendationStatusBadge,
  TableSkeleton,
} from "../components/ui";
import { recommendationsApi } from "../lib/api";
import { dateTime, relativeTime } from "../lib/format";

const statusFilters = [
  ["", "Todas"],
  ["pending_review", "Por revisar"],
  ["approved", "Aprobadas"],
  ["rejected", "Rechazadas"],
  ["superseded", "Reemplazadas"],
] as const;

export function RecommendationsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(searchParams.get("status") ?? "");
  const [page, setPage] = useState(1);
  const findingId = searchParams.get("finding_id") ?? undefined;
  const query = useQuery({
    queryKey: ["recommendations", "list", status, findingId, page],
    queryFn: () =>
      recommendationsApi.list({
        status: status || undefined,
        finding_id: findingId,
        page,
        page_size: 20,
      }),
    placeholderData: keepPreviousData,
  });

  return (
    <>
      <PageHeader
        kicker="Asistencia con revisión humana"
        title="Recomendaciones IA"
        description="Planes de corrección generados con LangChain y Ollama. Ningún comando se ejecuta desde la plataforma; toda propuesta requiere revisión y aprobación."
      />

      <div className="mb-5 flex flex-wrap items-center gap-1.5">
        {statusFilters.map(([value, label]) => (
          <button
            key={value}
            onClick={() => {
              setStatus(value);
              setPage(1);
            }}
            className={clsx(
              "rounded-full border px-3.5 py-1.5 text-[11px] font-semibold transition",
              status === value
                ? "border-ink-900 bg-ink-900 text-white"
                : "border-line bg-white text-slate-500 hover:border-slate-300 hover:text-slate-800",
            )}
          >
            {label}
          </button>
        ))}
        {findingId && (
          <Link to="/recommendations" className="ml-auto text-[11px] font-semibold text-accent-700 hover:underline">
            Quitar filtro de hallazgo
          </Link>
        )}
      </div>

      {query.isLoading ? (
        <TableSkeleton rows={6} cols={6} />
      ) : query.isError ? (
        <ErrorState message="No se pudieron consultar las recomendaciones." onRetry={() => void query.refetch()} />
      ) : query.data?.items.length ? (
        <div className="table-shell">
          <div className="overflow-x-auto">
            <table className="data-table min-w-[960px]">
              <thead>
                <tr>
                  <th>Propuesta</th>
                  <th>Servidor</th>
                  <th>Validación</th>
                  <th>Estado</th>
                  <th>Modelo</th>
                  <th>Creada</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((recommendation) => (
                  <tr key={recommendation.id} className="clickable" onClick={() => navigate(`/recommendations/${recommendation.id}`)}>
                    <td>
                      <div className="flex items-start gap-2.5">
                        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-50 text-violet-600">
                          <Sparkles className="h-4 w-4" />
                        </span>
                        <div className="min-w-0">
                          <p className="max-w-[330px] truncate text-xs font-semibold text-ink-900">
                            {recommendation.payload.problem || recommendation.finding_title || "Propuesta de corrección"}
                          </p>
                          <p className="mt-0.5 text-[10px] text-slate-400">
                            {recommendation.control_code ?? "Control"} · {recommendation.payload.commands.length} comando(s)
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="text-xs">{recommendation.server_name ?? "—"}</td>
                    <td>
                      <Badge
                        tone={
                          recommendation.validation_status === "dangerous"
                            ? "danger"
                            : recommendation.validation_status === "warnings"
                              ? "warning"
                              : "neutral"
                        }
                      >
                        {recommendation.validation_status === "dangerous"
                          ? "Comandos peligrosos"
                          : recommendation.validation_status === "warnings"
                            ? "Con advertencias"
                            : "Sin verificación"}
                      </Badge>
                    </td>
                    <td><RecommendationStatusBadge status={recommendation.status} /></td>
                    <td>
                      <p className="text-[11px] font-medium text-slate-600">{recommendation.model}</p>
                      <p className="text-[10px] text-slate-400">{recommendation.provider}</p>
                    </td>
                    <td className="whitespace-nowrap text-xs text-slate-500">{relativeTime(recommendation.created_at)}</td>
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
            icon={status === "pending_review" ? <ShieldAlert className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
            title="Sin recomendaciones"
            description="Genere una propuesta desde un hallazgo abierto. Si Ollama no está disponible, la auditoría continúa funcionando."
            action={
              <Link to="/findings" className="text-[11px] font-semibold text-accent-700 hover:underline">
                Ir a hallazgos
              </Link>
            }
          />
        </div>
      )}
    </>
  );
}
