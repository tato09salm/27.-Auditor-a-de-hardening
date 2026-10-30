import { keepPreviousData, useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { ChevronDown, ChevronRight, ScrollText, ShieldCheck } from "lucide-react";
import { useState } from "react";
import {
  Badge,
  EmptyState,
  ErrorState,
  PageHeader,
  Pagination,
  SearchField,
  TableSkeleton,
} from "../components/ui";
import { logsApi } from "../lib/api";
import { dateTime, prettyJson } from "../lib/format";
import { useDebouncedValue } from "../lib/hooks";
import type { AuditLog } from "../types";

function LogRow({ entry }: { entry: AuditLog }) {
  const [open, setOpen] = useState(false);
  const hasChanges = Object.keys(entry.changes ?? {}).length > 0;
  return (
    <>
      <tr className={clsx(hasChanges && "clickable")} onClick={() => hasChanges && setOpen((current) => !current)}>
        <td className="whitespace-nowrap text-[11px] text-slate-500">
          {dateTime(entry.created_at)}
          {entry.request_id && <span className="block font-mono text-[9px] text-slate-300">{entry.request_id.slice(0, 12)}</span>}
        </td>
        <td>
          <p className="text-xs font-semibold text-ink-900">{entry.user_name ?? (entry.api_token_id ? "Automatización n8n" : "Sistema")}</p>
          <p className="text-[10px] text-slate-400">{entry.ip_address ?? "sin IP"}</p>
        </td>
        <td><Badge tone="neutral">{entry.module}</Badge></td>
        <td>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-slate-700">{entry.action}</span>
            {hasChanges && (open ? <ChevronDown className="h-3.5 w-3.5 text-slate-300" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-300" />)}
          </div>
          {entry.resource_type && <p className="mt-0.5 text-[9px] text-slate-400">{entry.resource_type} · {entry.resource_id?.slice(0, 8)}</p>}
        </td>
        <td>
          <Badge tone={entry.result === "success" ? "success" : entry.result === "denied" ? "danger" : "warning"}>
            {entry.result}
          </Badge>
        </td>
      </tr>
      {open && hasChanges && (
        <tr>
          <td colSpan={5} className="!bg-slate-50 !px-5 !py-4">
            <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">Cambios registrados (secretos redactados)</p>
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-xl border border-line bg-white p-3 font-mono text-[10px] leading-5 text-slate-600">
              {prettyJson(entry.changes)}
            </pre>
          </td>
        </tr>
      )}
    </>
  );
}

export function AuditLogPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [module, setModule] = useState("");
  const [result, setResult] = useState("");
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["audit-logs", debouncedSearch, module, result, page],
    queryFn: () =>
      logsApi.list({
        action: debouncedSearch || undefined,
        module: module || undefined,
        result: result || undefined,
        page,
        page_size: 30,
      }),
    placeholderData: keepPreviousData,
  });

  return (
    <>
      <PageHeader
        kicker="Trazabilidad append-only"
        title="Bitácora"
        description="Accesos, cambios de servidores, ejecuciones, revisiones y reportes. Los registros no se pueden modificar ni eliminar desde la aplicación."
      />

      <div className="mb-5 flex flex-wrap items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 text-[11px] text-emerald-800">
        <ShieldCheck className="h-4 w-4" />
        Trigger PostgreSQL activo: <code className="font-mono text-[10px]">audit_logs</code> rechaza UPDATE y DELETE. Los secretos se redactan antes de persistir.
      </div>

      <div className="card mb-5 p-3">
        <div className="grid gap-2.5 sm:grid-cols-3">
          <SearchField value={search} onChange={(value) => { setSearch(value); setPage(1); }} placeholder="Buscar por acción…" />
          <select className="select py-2 text-xs" value={module} onChange={(event) => { setModule(event.target.value); setPage(1); }}>
            <option value="">Todos los módulos</option>
            {["auth", "servers", "audits", "findings", "recommendations", "reports", "users", "schedules", "settings", "automation", "setup", "profiles"].map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
          <select className="select py-2 text-xs" value={result} onChange={(event) => { setResult(event.target.value); setPage(1); }}>
            <option value="">Todos los resultados</option>
            <option value="success">Éxito</option>
            <option value="failure">Fallo</option>
            <option value="denied">Denegado</option>
          </select>
        </div>
      </div>

      {query.isLoading ? (
        <TableSkeleton rows={10} cols={5} />
      ) : query.isError ? (
        <ErrorState message="No se pudo consultar la bitácora." onRetry={() => void query.refetch()} />
      ) : query.data?.items.length ? (
        <div className="table-shell">
          <div className="overflow-x-auto">
            <table className="data-table min-w-[920px]">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Actor</th>
                  <th>Módulo</th>
                  <th>Acción / recurso</th>
                  <th>Resultado</th>
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((entry) => <LogRow key={entry.id} entry={entry} />)}
              </tbody>
            </table>
          </div>
          <Pagination page={query.data.page} pageSize={query.data.page_size} total={query.data.total} onPageChange={setPage} />
        </div>
      ) : (
        <div className="card">
          <EmptyState icon={<ScrollText className="h-5 w-5" />} title="Sin registros" description="No hay eventos que coincidan con los filtros." />
        </div>
      )}
    </>
  );
}
