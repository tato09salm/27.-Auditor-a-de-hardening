import { keepPreviousData, useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { ChevronRight, Plus, Server as ServerIcon, ShieldAlert, Wifi } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ServerFormModal } from "../components/ServerFormModal";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  PageHeader,
  Pagination,
  ScoreBar,
  ScoreLabel,
  SearchField,
  ServerStatusBadge,
  TableSkeleton,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { serversApi } from "../lib/api";
import { environmentLabel, relativeTime } from "../lib/format";
import { useDebouncedValue } from "../lib/hooks";
import type { Server } from "../types";

export function ServersPage() {
  const { hasPermission } = useAuth();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [environment, setEnvironment] = useState("");
  const [status, setStatus] = useState("");
  const [active, setActive] = useState("true");
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);

  const query = useQuery({
    queryKey: ["servers", "list", debouncedSearch, environment, status, active, page],
    queryFn: () =>
      serversApi.list({
        search: debouncedSearch || undefined,
        environment: environment || undefined,
        status: status || undefined,
        is_active: active === "" ? undefined : active,
        page,
        page_size: 20,
      }),
    placeholderData: keepPreviousData,
  });

  const canManage = hasPermission("servers:manage");

  function updateFilter(setter: (value: string) => void, value: string) {
    setter(value);
    setPage(1);
  }

  return (
    <>
      <PageHeader
        kicker="Inventario autorizado"
        title="Servidores"
        description="Objetivos registrados para auditoría. Cada conexión requiere autorización explícita y usa solo comprobaciones de lectura."
        actions={
          canManage ? (
            <Button icon={<Plus className="h-4 w-4" />} onClick={() => setFormOpen(true)}>
              Registrar servidor
            </Button>
          ) : undefined
        }
      />

      <div className="card mb-5 p-3">
        <div className="grid gap-2.5 lg:grid-cols-[1.4fr_repeat(3,minmax(0,0.65fr))]">
          <SearchField
            value={search}
            onChange={(value) => updateFilter(setSearch, value)}
            placeholder="Buscar por nombre, hostname o IP…"
          />
          <select className="select py-2 text-xs" value={environment} onChange={(event) => updateFilter(setEnvironment, event.target.value)} aria-label="Entorno">
            <option value="">Todos los entornos</option>
            <option value="production">Producción</option>
            <option value="staging">Pruebas</option>
            <option value="development">Desarrollo</option>
          </select>
          <select className="select py-2 text-xs" value={status} onChange={(event) => updateFilter(setStatus, event.target.value)} aria-label="Estado">
            <option value="">Todos los estados</option>
            <option value="online">En línea</option>
            <option value="offline">Sin conexión</option>
            <option value="auth_error">Error de autenticación</option>
            <option value="pending">Pendiente</option>
            <option value="disabled">Desactivado</option>
          </select>
          <select className="select py-2 text-xs" value={active} onChange={(event) => updateFilter(setActive, event.target.value)} aria-label="Activo">
            <option value="true">Solo activos</option>
            <option value="false">Solo inactivos</option>
            <option value="">Todos</option>
          </select>
        </div>
      </div>

      {query.isLoading ? (
        <TableSkeleton rows={7} cols={6} />
      ) : query.isError ? (
        <ErrorState message="No se pudo consultar el inventario." onRetry={() => void query.refetch()} />
      ) : (
        <div className="table-shell">
          <div className="flex items-center justify-between border-b border-line bg-white px-4 py-3">
            <p className="text-xs font-semibold text-slate-500">
              {query.data?.total ?? 0} servidor(es) en el inventario
            </p>
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <Wifi className="h-3.5 w-3.5" />
              Último chequeo de conectividad por servidor
            </div>
          </div>
          {query.data?.items.length ? (
            <>
              <div className="overflow-x-auto">
                <table className="data-table min-w-[980px]">
                  <thead>
                    <tr>
                      <th>Servidor</th>
                      <th>Destino</th>
                      <th>Entorno</th>
                      <th>Estado</th>
                      <th>Cumplimiento</th>
                      <th>Hallazgos</th>
                      <th>Última auditoría</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {query.data.items.map((server) => (
                      <tr key={server.id} className="clickable" onClick={() => navigate(`/servers/${server.id}`)}>
                        <td>
                          <div className="flex items-start gap-3">
                            <span
                              className={clsx(
                                "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl",
                                server.is_simulated ? "bg-amber-50 text-amber-600" : "bg-slate-100 text-slate-500",
                              )}
                            >
                              <ServerIcon className="h-4 w-4" />
                            </span>
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-1.5">
                                <span className="max-w-[220px] truncate text-xs font-bold text-ink-900">
                                  {server.name}
                                </span>
                                {server.is_simulated && <Badge tone="warning">Simulado</Badge>}
                                {!server.authorization_confirmed && <Badge tone="danger">Sin autorizar</Badge>}
                              </div>
                              <p className="mt-0.5 truncate text-[10px] text-slate-400">
                                {server.os_family} {server.os_version} · {server.default_profile_name ?? "Sin perfil"}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td>
                          <p className="font-mono text-[11px] text-slate-700">{server.ip_address}:{server.port}</p>
                          <p className="mt-0.5 text-[10px] text-slate-400">{server.hostname}</p>
                        </td>
                        <td>
                          <span className="text-xs text-slate-600">{environmentLabel[server.environment]}</span>
                        </td>
                        <td>
                          <ServerStatusBadge status={server.status} />
                        </td>
                        <td className="min-w-[126px]">
                          <div className="flex items-center justify-between gap-2">
                            <ScoreLabel score={server.last_score} />
                            <span className="text-[10px] text-slate-400">score</span>
                          </div>
                          <ScoreBar score={server.last_score} className="mt-1.5" />
                        </td>
                        <td>
                          <div className="flex items-center gap-1.5">
                            {server.active_findings > 0 ? (
                              <>
                                <ShieldAlert className="h-3.5 w-3.5 text-red-500" />
                                <span className="text-xs font-semibold text-slate-700">{server.active_findings}</span>
                              </>
                            ) : (
                              <span className="text-[10px] text-slate-400">Sin activos</span>
                            )}
                          </div>
                        </td>
                        <td className="whitespace-nowrap text-xs text-slate-500">
                          {server.last_audit_at ? relativeTime(server.last_audit_at) : "Nunca"}
                        </td>
                        <td>
                          <ChevronRight className="h-4 w-4 text-slate-300" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={query.data.page}
                pageSize={query.data.page_size}
                total={query.data.total}
                onPageChange={setPage}
              />
            </>
          ) : (
            <EmptyState
              icon={<ServerIcon className="h-5 w-5" />}
              title="No hay servidores que coincidan"
              description={
                search || environment || status
                  ? "Ajuste los filtros o registre un nuevo servidor autorizado."
                  : "Registre el primer servidor y confirme la autorización explícita para auditarlo."
              }
              action={
                canManage ? (
                  <Button icon={<Plus className="h-4 w-4" />} onClick={() => setFormOpen(true)}>
                    Registrar servidor
                  </Button>
                ) : undefined
              }
            />
          )}
        </div>
      )}

      <ServerFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={() => void query.refetch()}
      />
    </>
  );
}
