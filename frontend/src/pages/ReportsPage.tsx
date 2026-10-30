import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import {
  Download,
  FileSpreadsheet,
  FileText,
  FileType2,
  Loader2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  FormField,
  PageHeader,
  Pagination,
  SectionHeader,
  TableSkeleton,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, auditsApi, downloadReport, reportsApi, serversApi } from "../lib/api";
import { bytes, dateTime } from "../lib/format";
import type { Report } from "../types";

const formatMeta = {
  pdf: { label: "PDF", icon: FileText, tone: "bg-red-50 text-red-600" },
  docx: { label: "Word", icon: FileType2, tone: "bg-blue-50 text-blue-600" },
  xlsx: { label: "Excel", icon: FileSpreadsheet, tone: "bg-emerald-50 text-emerald-600" },
} as const;

export function ReportsPage() {
  const { hasPermission } = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const initialRun = searchParams.get("run_id") ?? "";
  const [page, setPage] = useState(1);
  const [type, setType] = useState<"technical" | "executive">(initialRun ? "technical" : "executive");
  const [format, setFormat] = useState<"pdf" | "docx" | "xlsx">("pdf");
  const [runId, setRunId] = useState(initialRun);
  const [serverId, setServerId] = useState(searchParams.get("server_id") ?? "");
  const [periodStart, setPeriodStart] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [periodEnd, setPeriodEnd] = useState(() => new Date().toISOString().slice(0, 10));
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  const reportsQuery = useQuery({
    queryKey: ["reports", page],
    queryFn: () => reportsApi.list({ page, page_size: 15 }),
    placeholderData: keepPreviousData,
  });
  const runsQuery = useQuery({
    queryKey: ["audits", "reports-picker"],
    queryFn: () => auditsApi.list({ status: "completed", page_size: 100 }),
    enabled: hasPermission("reports:generate"),
  });
  const serversQuery = useQuery({
    queryKey: ["servers", "reports-picker"],
    queryFn: () => serversApi.list({ page_size: 200 }),
    enabled: hasPermission("reports:generate"),
  });

  useEffect(() => {
    if (initialRun && runsQuery.data?.items.some((run) => run.id === initialRun)) {
      setRunId(initialRun);
      setType("technical");
    }
  }, [initialRun, runsQuery.data]);

  const generateMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = { report_type: type, format };
      if (type === "technical") {
        payload.audit_run_id = runId;
      } else {
        payload.server_id = serverId || null;
        payload.period_start = `${periodStart}T00:00:00Z`;
        payload.period_end = `${periodEnd}T23:59:59Z`;
      }
      return reportsApi.create(payload);
    },
    onSuccess: async (report) => {
      notify({
        tone: "success",
        title: "Reporte generado",
        message: "El archivo se descargará y quedará disponible en el histórico.",
      });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      try {
        await downloadReport(report);
      } catch {
        notify({ tone: "info", title: "Reporte generado", message: "Use el botón Descargar de la tabla." });
      }
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.message : "No fue posible generar el reporte."),
  });

  const canGenerate = hasPermission("reports:generate");
  const canSubmit =
    type === "technical" ? Boolean(runId) : Boolean(periodStart && periodEnd && periodStart <= periodEnd);

  async function handleDownload(report: Report) {
    setDownloading(report.id);
    try {
      await downloadReport(report);
    } catch (err) {
      notify({
        tone: "error",
        title: "No se pudo descargar",
        message: err instanceof ApiError ? err.message : "El archivo puede haber sido removido.",
      });
    } finally {
      setDownloading(null);
    }
  }

  return (
    <>
      <PageHeader
        kicker="Entrega formal"
        title="Reportes"
        description="Informes técnicos y ejecutivos en PDF, Word y Excel. Incluyen limitaciones y no contienen contraseñas, claves ni tokens."
      />

      <div className="grid gap-5 xl:grid-cols-12">
        {canGenerate && (
          <Card className="p-5 xl:col-span-4">
            <SectionHeader title="Generar reporte" description="La generación usa datos reales de PostgreSQL." />
            {error && <Alert tone="danger" className="mt-4">{error}</Alert>}
            <div className="mt-4 space-y-4">
              <div>
                <span className="label">Tipo de informe</span>
                <div className="grid grid-cols-2 gap-2">
                  {(["technical", "executive"] as const).map((option) => (
                    <button
                      key={option}
                      className={clsx(
                        "rounded-xl border px-3 py-2.5 text-left text-xs font-semibold transition",
                        type === option
                          ? "border-accent-500 bg-cyan-50 text-accent-800"
                          : "border-line bg-white text-slate-500 hover:border-slate-300",
                      )}
                      onClick={() => setType(option)}
                    >
                      {option === "technical" ? "Técnico" : "Ejecutivo"}
                      <span className="mt-0.5 block text-[9px] font-normal text-slate-400">
                        {option === "technical" ? "Una ejecución y sus evidencias" : "Periodo consolidado"}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {type === "technical" ? (
                <FormField label="Auditoría" required>
                  <select className="select" value={runId} onChange={(event) => setRunId(event.target.value)}>
                    <option value="">Seleccione una auditoría completada</option>
                    {(runsQuery.data?.items ?? []).map((run) => (
                      <option key={run.id} value={run.id}>
                        {run.server_name} · {dateTime(run.created_at)}
                      </option>
                    ))}
                  </select>
                </FormField>
              ) : (
                <>
                  <FormField label="Servidor (opcional)">
                    <select className="select" value={serverId} onChange={(event) => setServerId(event.target.value)}>
                      <option value="">Todos los servidores</option>
                      {(serversQuery.data?.items ?? []).map((server) => (
                        <option key={server.id} value={server.id}>{server.name}</option>
                      ))}
                    </select>
                  </FormField>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="Desde" required>
                      <input type="date" className="input" value={periodStart} max={periodEnd} onChange={(event) => setPeriodStart(event.target.value)} />
                    </FormField>
                    <FormField label="Hasta" required>
                      <input type="date" className="input" value={periodEnd} min={periodStart} max={new Date().toISOString().slice(0, 10)} onChange={(event) => setPeriodEnd(event.target.value)} />
                    </FormField>
                  </div>
                </>
              )}

              <div>
                <span className="label">Formato</span>
                <div className="grid grid-cols-3 gap-2">
                  {(["pdf", "docx", "xlsx"] as const).map((value) => {
                    const meta = formatMeta[value];
                    const Icon = meta.icon;
                    return (
                      <button
                        key={value}
                        className={clsx(
                          "flex flex-col items-center gap-1.5 rounded-xl border px-2 py-3 text-[10px] font-semibold transition",
                          format === value
                            ? "border-accent-500 bg-cyan-50 text-accent-800"
                            : "border-line text-slate-500 hover:border-slate-300",
                        )}
                        onClick={() => setFormat(value)}
                      >
                        <Icon className="h-4 w-4" />
                        {meta.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <Button
                className="w-full"
                loading={generateMutation.isPending}
                disabled={!canSubmit}
                icon={<Sparkles className="h-4 w-4" />}
                onClick={() => {
                  setError(null);
                  generateMutation.mutate();
                }}
              >
                Generar y descargar
              </Button>
              <p className="text-[10px] leading-5 text-slate-400">
                El reporte técnico requiere una auditoría completada. El ejecutivo consolida el periodo y
                compara con el periodo anterior.
              </p>
            </div>
          </Card>
        )}

        <Card className={clsx("overflow-hidden", canGenerate ? "xl:col-span-8" : "xl:col-span-12")}>
          <div className="flex items-center justify-between p-5 pb-2">
            <SectionHeader title="Histórico de reportes" description="Archivos generados, con checksum SHA-256." />
            <ShieldCheck className="h-5 w-5 text-emerald-500" />
          </div>
          {reportsQuery.isLoading ? (
            <div className="p-5"><TableSkeleton rows={5} cols={5} /></div>
          ) : reportsQuery.isError ? (
            <div className="p-5"><ErrorState message="No se pudo consultar el histórico." onRetry={() => void reportsQuery.refetch()} /></div>
          ) : reportsQuery.data?.items.length ? (
            <>
              <div className="overflow-x-auto">
                <table className="data-table min-w-[820px]">
                  <thead>
                    <tr>
                      <th>Reporte</th>
                      <th>Tipo</th>
                      <th>Servidor</th>
                      <th>Generado</th>
                      <th>Tamaño</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {reportsQuery.data.items.map((report) => {
                      const meta = formatMeta[report.format];
                      const Icon = meta.icon;
                      return (
                        <tr key={report.id}>
                          <td>
                            <div className="flex items-center gap-2.5">
                              <span className={clsx("flex h-8 w-8 items-center justify-center rounded-lg", meta.tone)}>
                                <Icon className="h-4 w-4" />
                              </span>
                              <div>
                                <p className="max-w-[240px] truncate text-xs font-semibold text-ink-900">{report.file_name}</p>
                                <p className="font-mono text-[9px] text-slate-400">SHA256 {report.sha256.slice(0, 12)}…</p>
                              </div>
                            </div>
                          </td>
                          <td>
                            <Badge tone={report.report_type === "technical" ? "info" : "accent"}>
                              {report.report_type === "technical" ? "Técnico" : "Ejecutivo"}
                            </Badge>
                          </td>
                          <td className="text-xs">{report.server_name ?? "Organización"}</td>
                          <td className="whitespace-nowrap text-xs text-slate-500">
                            {dateTime(report.created_at)}
                            <span className="block text-[9px] text-slate-400">{report.generated_by_name}</span>
                          </td>
                          <td className="text-xs">{bytes(report.size_bytes)}</td>
                          <td>
                            <Button
                              variant="secondary"
                              size="sm"
                              loading={downloading === report.id}
                              icon={downloading === report.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                              onClick={() => void handleDownload(report)}
                            >
                              Descargar
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <Pagination page={reportsQuery.data.page} pageSize={reportsQuery.data.page_size} total={reportsQuery.data.total} onPageChange={setPage} />
            </>
          ) : (
            <EmptyState
              icon={<FileText className="h-5 w-5" />}
              title="Sin reportes generados"
              description="Genere un informe técnico o ejecutivo para conservar evidencia formal."
            />
          )}
        </Card>
      </div>
    </>
  );
}
