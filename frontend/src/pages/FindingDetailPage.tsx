import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Bug,
  CheckCircle2,
  Circle,
  Clock3,
  FileSearch,
  ListChecks,
  MessageSquareText,
  Server as ServerIcon,
  Sparkles,
  Terminal,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Alert,
  Badge,
  Button,
  Card,
  EvidenceValue,
  FindingStatusBadge,
  FormField,
  Modal,
  PageLoader,
  RecommendationStatusBadge,
  SectionHeader,
  SeverityBadge,
  ErrorState,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, findingsApi, recommendationsApi } from "../lib/api";
import {
  dateTime,
  findingStatusLabel,
  prettyJson,
  relativeTime,
  statusLabel,
} from "../lib/format";
import type { FindingStatus } from "../types";

const transitions: Record<FindingStatus, FindingStatus[]> = {
  detected: ["in_review", "correction_planned", "risk_accepted", "false_positive"],
  in_review: ["detected", "correction_planned", "risk_accepted", "false_positive"],
  correction_planned: ["in_review", "fixed_pending_validation", "risk_accepted"],
  fixed_pending_validation: ["correction_planned", "resolved", "risk_accepted"],
  risk_accepted: ["detected", "resolved"],
  false_positive: ["detected"],
  resolved: ["detected"],
};

const workflow = ["detected", "in_review", "correction_planned", "fixed_pending_validation", "resolved"] as const;

export function FindingDetailPage() {
  const { findingId = "" } = useParams();
  const { hasPermission, user } = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [statusOpen, setStatusOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState<FindingStatus>("in_review");
  const [comment, setComment] = useState("");
  const [resolutionNote, setResolutionNote] = useState("");
  const [riskUntil, setRiskUntil] = useState("");
  const [dialogError, setDialogError] = useState<string | null>(null);

  const findingQuery = useQuery({
    queryKey: ["finding", findingId],
    queryFn: () => findingsApi.get(findingId),
    enabled: Boolean(findingId),
  });
  const recommendationsQuery = useQuery({
    queryKey: ["recommendations", "finding", findingId],
    queryFn: () => recommendationsApi.list({ finding_id: findingId, page_size: 20 }),
    enabled: Boolean(findingId),
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      findingsApi.update(findingId, {
        status: targetStatus,
        comment: comment.trim() || undefined,
        resolution_note: resolutionNote.trim() || undefined,
        risk_acceptance_until: targetStatus === "risk_accepted" ? riskUntil || undefined : undefined,
      }),
    onSuccess: () => {
      notify({ tone: "success", title: "Hallazgo actualizado", message: "El cambio quedó registrado en el historial." });
      setStatusOpen(false);
      setComment("");
      setResolutionNote("");
      setRiskUntil("");
      void queryClient.invalidateQueries({ queryKey: ["finding", findingId] });
      void queryClient.invalidateQueries({ queryKey: ["findings"] });
    },
    onError: (error) => {
      setDialogError(error instanceof ApiError ? error.message : "No fue posible actualizar el hallazgo.");
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => findingsApi.generateRecommendation(findingId),
    onSuccess: (result) => {
      notify({
        tone: "success",
        title: "Propuesta generada",
        message: "Requiere revisión humana. Ningún comando se ejecutó.",
      });
      void queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      navigate(`/recommendations/${result.recommendation.id}`);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 503) {
        notify({
          tone: "error",
          title: "IA no disponible",
          message: "Ollama no responde. La auditoría y el resto de la plataforma siguen disponibles.",
        });
      } else {
        notify({
          tone: "error",
          title: "No se pudo generar la propuesta",
          message: error instanceof ApiError ? error.message : "Error inesperado.",
        });
      }
    },
  });

  const availableTransitions = useMemo(
    () => (findingQuery.data ? transitions[findingQuery.data.status] : []),
    [findingQuery.data],
  );

  if (findingQuery.isLoading) return <PageLoader label="Cargando hallazgo…" />;
  if (findingQuery.isError || !findingQuery.data) {
    return <ErrorState title="Hallazgo no disponible" message="No existe o pertenece a otra organización." />;
  }
  const finding = findingQuery.data;
  const evidence = finding.evidence ?? {};
  const stdout = typeof evidence.stdout === "string" ? evidence.stdout : "";
  const activeIndex = workflow.indexOf(finding.status as (typeof workflow)[number]);
  const isClosed = finding.status === "resolved" || finding.status === "false_positive";
  const canManage = hasPermission("findings:manage");
  const canGenerate = hasPermission("recommendations:generate") && !isClosed;

  function openStatusModal() {
    setTargetStatus(availableTransitions[0] ?? "in_review");
    setComment("");
    setResolutionNote(finding.resolution_note ?? "");
    setRiskUntil(finding.risk_acceptance_until ?? "");
    setDialogError(null);
    setStatusOpen(true);
  }

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <Link to="/findings" className="inline-flex items-center gap-1 font-medium hover:text-slate-700">
          <ArrowLeft className="h-3.5 w-3.5" /> Hallazgos
        </Link>
        <span>/</span>
        <span className="font-mono font-semibold text-slate-600">{finding.control_code}</span>
      </div>

      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-red-100 bg-red-50 text-red-600">
            <Bug className="h-6 w-6" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-ink-950 sm:text-3xl">{finding.title}</h1>
              <SeverityBadge severity={finding.severity} />
              <FindingStatusBadge status={finding.status} />
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {finding.server_name} ·{" "}
              <span className="font-mono text-xs">{finding.cis_reference ?? "Control interno"}</span> ·{" "}
              detectado {relativeTime(finding.first_seen_at)}
            </p>
            <div className="mt-2 flex flex-wrap gap-4 text-[11px] text-slate-400">
              <span>Ocurrencias: <b className="text-slate-600">{finding.occurrence_count}</b></span>
              <span>Responsable: <b className="text-slate-600">{finding.owner_name ?? "sin asignar"}</b></span>
              <span>Vence: <b className="text-slate-600">{finding.due_date ?? "sin fecha"}</b></span>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" icon={<ServerIcon className="h-4 w-4" />} onClick={() => navigate(`/servers/${finding.server_id}`)}>
            Ver servidor
          </Button>
          {canManage && availableTransitions.length > 0 && (
            <Button variant="secondary" icon={<ListChecks className="h-4 w-4" />} onClick={openStatusModal}>
              Actualizar estado
            </Button>
          )}
          {canGenerate && (
            <Button
              icon={<Sparkles className="h-4 w-4" />}
              loading={generateMutation.isPending}
              onClick={() => generateMutation.mutate()}
            >
              Generar recomendación IA
            </Button>
          )}
        </div>
      </div>

      {finding.status === "risk_accepted" && (
        <Alert tone="warning" className="mb-5" title="Riesgo aceptado temporalmente">
          Aceptado hasta {finding.risk_acceptance_until ?? "sin fecha"}. La aceptación no elimina el
          incumplimiento y debe revisarse al vencer.
        </Alert>
      )}
      {finding.status === "false_positive" && (
        <Alert tone="info" className="mb-5" title="Falso positivo documentado">
          {finding.resolution_note ?? "Documente la justificación de esta clasificación."}
        </Alert>
      )}

      <div className="grid gap-5 xl:grid-cols-12">
        <div className="space-y-5 xl:col-span-8">
          <Card className="p-5">
            <SectionHeader title="Ciclo de vida" description="El estado refleja el seguimiento operativo del hallazgo." />
            <div className="mt-6 flex items-start">
              {workflow.map((status, index) => {
                const current = activeIndex >= 0 && index <= activeIndex;
                const isCurrent = finding.status === status;
                return (
                  <div key={status} className="flex flex-1 flex-col items-center text-center">
                    <div className="flex w-full items-center">
                      <div className={clsx("h-0.5 flex-1", index === 0 ? "bg-transparent" : current ? "bg-emerald-400" : "bg-slate-200")} />
                      <span
                        className={clsx(
                          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-[10px] font-bold",
                          isCurrent
                            ? "border-accent-500 bg-accent-500 text-white shadow-[0_0_0_4px_rgba(6,182,212,0.12)]"
                            : current
                              ? "border-emerald-400 bg-emerald-50 text-emerald-600"
                              : "border-slate-200 bg-white text-slate-300",
                        )}
                      >
                        {current ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3 w-3" />}
                      </span>
                      <div className={clsx("h-0.5 flex-1", index === workflow.length - 1 ? "bg-transparent" : current ? "bg-emerald-400" : "bg-slate-200")} />
                    </div>
                    <p className={clsx("mt-2 max-w-[90px] text-[9px] font-semibold leading-4", isCurrent ? "text-ink-900" : "text-slate-400")}>
                      {findingStatusLabel[status]}
                    </p>
                  </div>
                );
              })}
            </div>
            {activeIndex < 0 && (
              <div className="mt-4 rounded-xl border border-line bg-slate-50 p-3 text-xs text-slate-600">
                Estado especial: <b>{findingStatusLabel[finding.status]}</b>. Use “Actualizar estado” para
                reabrir o cambiar el tratamiento.
              </div>
            )}
          </Card>

          <Card className="p-5">
            <SectionHeader title="Evidencia del último hallazgo" description={`Detectado por última vez ${dateTime(finding.last_seen_at)}.`} />
            <div className="mt-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Resultado observado</p>
              <p className="mt-1.5 text-xs leading-6 text-slate-700">{finding.observed_value ?? "Sin observación registrada."}</p>
            </div>
            {stdout && (
              <div className="mt-4">
                <p className="mb-2 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  <Terminal className="h-3.5 w-3.5" /> Salida técnica
                </p>
                <EvidenceValue value={stdout} />
              </div>
            )}
            <details className="mt-4 rounded-xl border border-line bg-slate-50/60 p-3">
              <summary className="cursor-pointer text-[10px] font-bold uppercase tracking-wider text-slate-500">
                Evidencia estructurada completa
              </summary>
              <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] leading-5 text-slate-600">
                {prettyJson(evidence)}
              </pre>
            </details>
            <div className="mt-4 rounded-xl border border-cyan-100 bg-cyan-50/50 p-3.5">
              <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-cyan-800">
                <FileSearch className="h-3.5 w-3.5" /> Guía de referencia del control
              </p>
              <p className="mt-1.5 text-xs leading-6 text-cyan-900/80">
                {finding.description}
              </p>
              <p className="mt-2 text-[10px] leading-5 text-cyan-900/60">
                El detalle del criterio verificable y los comandos de referencia están en los resultados
                de la auditoría de origen.
              </p>
              {finding.recommendation_count > 0 && (
                <Link to={`/recommendations?finding_id=${finding.id}`} className="mt-3 inline-flex items-center gap-1 text-[11px] font-semibold text-accent-700 hover:underline">
                  Revisar {finding.recommendation_count} propuesta(s) de IA <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              )}
            </div>
          </Card>

          <Card className="overflow-hidden">
            <div className="flex items-center justify-between p-5 pb-2">
              <SectionHeader title="Propuestas de corrección" description="Planes estructurados que requieren revisión humana." />
              <Link to={`/recommendations?finding_id=${finding.id}`} className="text-[11px] font-semibold text-accent-700 hover:underline">
                Ver todas
              </Link>
            </div>
            {recommendationsQuery.isLoading ? (
              <div className="px-5 py-8 text-center text-xs text-slate-400">Cargando propuestas…</div>
            ) : recommendationsQuery.data?.items.length ? (
              <div className="divide-y divide-line/70">
                {recommendationsQuery.data.items.slice(0, 5).map((recommendation) => (
                  <button
                    key={recommendation.id}
                    className="flex w-full items-center gap-3 px-5 py-3.5 text-left transition hover:bg-slate-50"
                    onClick={() => navigate(`/recommendations/${recommendation.id}`)}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-50 text-violet-600">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-semibold text-ink-900">
                        {recommendation.payload.problem || "Propuesta de corrección"}
                      </p>
                      <p className="mt-0.5 text-[10px] text-slate-400">
                        {recommendation.provider} · {recommendation.model} · {relativeTime(recommendation.created_at)}
                      </p>
                    </div>
                    <RecommendationStatusBadge status={recommendation.status} />
                  </button>
                ))}
              </div>
            ) : (
              <div className="px-5 pb-5">
                <div className="rounded-xl border border-dashed border-line bg-slate-50/60 p-4 text-center">
                  <p className="text-xs font-semibold text-slate-600">Sin propuestas de IA</p>
                  <p className="mt-1 text-[11px] leading-5 text-slate-400">
                    {canGenerate
                      ? "Genere una propuesta contextualizada. No se ejecutará ningún comando."
                      : "Un analista con permiso puede generar una propuesta para este hallazgo."}
                  </p>
                </div>
              </div>
            )}
          </Card>

          <Card className="p-5">
            <SectionHeader title="Historial de cambios" description="Eventos registrados en el ciclo de vida." />
            <div className="mt-4 space-y-0">
              {finding.events.length ? (
                finding.events
                  .slice()
                  .reverse()
                  .map((event, index) => (
                    <div key={event.id} className="relative flex gap-3 pb-4">
                      {index < finding.events.length - 1 && (
                        <span className="absolute left-[11px] top-6 h-full w-px bg-line" />
                      )}
                      <span className="relative z-10 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-line bg-white text-slate-400">
                        <Clock3 className="h-3 w-3" />
                      </span>
                      <div className="min-w-0 pt-0.5">
                        <p className="text-xs font-semibold text-slate-700">
                          {event.event_type === "status_changed"
                            ? `Estado: ${event.from_status ? statusLabel[event.from_status] ?? event.from_status : "—"} → ${event.to_status ? statusLabel[event.to_status] ?? event.to_status : "—"}`
                            : event.event_type === "created"
                              ? "Hallazgo creado"
                              : event.event_type.replaceAll("_", " ")}
                        </p>
                        {event.comment && <p className="mt-0.5 text-[11px] leading-5 text-slate-500">{event.comment}</p>}
                        <p className="mt-0.5 text-[10px] text-slate-400">
                          {dateTime(event.created_at)} · {event.actor_name ?? "sistema"}
                        </p>
                      </div>
                    </div>
                  ))
              ) : (
                <p className="text-xs text-slate-400">Sin eventos registrados.</p>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-5 xl:col-span-4">
          <Card className="p-5">
            <SectionHeader title="Datos del hallazgo" />
            <dl className="mt-4 space-y-3.5">
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Control</dt>
                <dd className="mt-1 text-xs font-semibold text-ink-900">{finding.control_code} · {finding.cis_reference ?? "interno"}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Categoría</dt>
                <dd className="mt-1 text-xs">{finding.category ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Primera detección</dt>
                <dd className="mt-1 text-xs">{dateTime(finding.first_seen_at)}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Última detección</dt>
                <dd className="mt-1 text-xs">{dateTime(finding.last_seen_at)}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Auditoría de origen</dt>
                <dd className="mt-1">
                  <Link to={`/audits/${finding.last_seen_run_id}`} className="text-xs font-semibold text-accent-700 hover:underline">
                    Ver ejecución
                  </Link>
                </dd>
              </div>
            </dl>
          </Card>

          <Card className="p-5">
            <SectionHeader title="Recomendación de tratamiento" />
            <div className="mt-3 space-y-2 text-[11px] leading-5 text-slate-500">
              <p className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" /> Priorice por severidad y exposición del servidor.</p>
              <p className="flex gap-2"><MessageSquareText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" /> Documente el cambio y valide con una nueva auditoría.</p>
              <p className="flex gap-2"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" /> No acepte riesgos sin fecha de revisión.</p>
            </div>
            <div className="mt-4 rounded-xl bg-ink-950 p-3 text-[10px] leading-5 text-slate-400">
              La plataforma no ejecuta correcciones. Los comandos sugeridos por IA nunca se aplican
              automáticamente.
            </div>
          </Card>
        </div>
      </div>

      <Modal
        open={statusOpen}
        onClose={() => setStatusOpen(false)}
        title="Actualizar estado del hallazgo"
        description="El cambio se registra con su usuario, fecha y comentario en el historial."
        footer={
          <>
            <Button variant="secondary" onClick={() => setStatusOpen(false)}>Cancelar</Button>
            <Button
              loading={updateMutation.isPending}
              disabled={
                (targetStatus === "risk_accepted" && (!riskUntil || comment.trim().length < 5)) ||
                (targetStatus === "false_positive" && resolutionNote.trim().length < 10) ||
                (targetStatus === "resolved" && resolutionNote.trim().length < 10)
              }
              onClick={() => {
                setDialogError(null);
                updateMutation.mutate();
              }}
            >
              Confirmar cambio
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {dialogError && <Alert tone="danger">{dialogError}</Alert>}
          <FormField label="Nuevo estado" required>
            <select className="select" value={targetStatus} onChange={(event) => setTargetStatus(event.target.value as FindingStatus)}>
              {availableTransitions.map((status) => (
                <option key={status} value={status}>{findingStatusLabel[status]}</option>
              ))}
            </select>
          </FormField>
          {targetStatus === "risk_accepted" && (
            <FormField label="Aceptación válida hasta" required hint="La fecha no puede estar vencida.">
              <input type="date" className="input" value={riskUntil} onChange={(event) => setRiskUntil(event.target.value)} />
            </FormField>
          )}
          {(targetStatus === "false_positive" || targetStatus === "resolved") && (
            <FormField
              label="Justificación / nota de cierre"
              required={targetStatus === "false_positive" || targetStatus === "resolved"}
              hint={
                targetStatus === "resolved"
                  ? "El cierre normal requiere una comprobación satisfactoria. Solo un administrador puede justificarlo sin ella."
                  : "Documente por qué este resultado no representa un riesgo real."
              }
            >
              <textarea className="textarea" value={resolutionNote} onChange={(event) => setResolutionNote(event.target.value)} maxLength={4000} />
            </FormField>
          )}
          <FormField label="Comentario de seguimiento">
            <textarea className="textarea" value={comment} onChange={(event) => setComment(event.target.value)} maxLength={2000} />
          </FormField>
          <div className="rounded-xl border border-line bg-slate-50 p-3 text-[10px] leading-5 text-slate-500">
            <Badge tone="neutral">Auditoría</Badge>{" "}
            Este cambio no modifica la configuración del servidor ni cierra automáticamente otros hallazgos.
          </div>
        </div>
      </Modal>
    </>
  );
}
