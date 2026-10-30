import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import {
  AlertTriangle,
  ArrowLeft,
  Ban,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Clock3,
  Copy,
  FileText,
  Info,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Terminal,
  UserCheck,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Alert,
  Badge,
  Button,
  Card,
  CopyButton,
  EmptyState,
  FormField,
  Modal,
  PageLoader,
  RecommendationStatusBadge,
  SectionHeader,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, recommendationsApi } from "../lib/api";
import { dateTime, percent, relativeTime } from "../lib/format";

const interruptionLabel: Record<string, string> = {
  low: "Bajo",
  medium: "Medio",
  high: "Alto",
  unknown: "Desconocido",
};

function validationTone(status: string): "danger" | "warning" | "neutral" {
  if (status === "dangerous") return "danger";
  if (status === "warnings") return "warning";
  return "neutral";
}

export function RecommendationDetailPage() {
  const { recommendationId = "" } = useParams();
  const { hasPermission } = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [reviewOpen, setReviewOpen] = useState(false);
  const [decision, setDecision] = useState<"approved" | "rejected">("approved");
  const [comments, setComments] = useState("");
  const [reviewError, setReviewError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["recommendation", recommendationId],
    queryFn: () => recommendationsApi.get(recommendationId),
    enabled: Boolean(recommendationId),
  });

  const reviewMutation = useMutation({
    mutationFn: () =>
      recommendationsApi.review(recommendationId, { decision, comments: comments.trim() }),
    onSuccess: () => {
      notify({
        tone: "success",
        title: decision === "approved" ? "Propuesta aprobada" : "Propuesta rechazada",
        message: "La decisión quedó registrada con su usuario y comentario.",
      });
      setReviewOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["recommendation", recommendationId] });
      void queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      void queryClient.invalidateQueries({ queryKey: ["finding"] });
    },
    onError: (error) => {
      setReviewError(error instanceof ApiError ? error.message : "No fue posible registrar la revisión.");
    },
  });

  if (query.isLoading) return <PageLoader label="Cargando recomendación…" />;
  if (query.isError || !query.data) {
    return (
      <div className="card">
        <EmptyState
          icon={<Sparkles className="h-5 w-5" />}
          title="Recomendación no disponible"
          description="El registro no existe o pertenece a otra organización."
          action={<Link to="/recommendations" className="text-xs font-semibold text-accent-700">Volver</Link>}
        />
      </div>
    );
  }
  const recommendation = query.data;
  const payload = recommendation.payload;
  const canReview = hasPermission("recommendations:review") && recommendation.status === "pending_review";
  const dangerous = recommendation.validation_status === "dangerous";
  const flagged = new Set(recommendation.flagged_commands.map((flag) => flag.command));

  function openReview(next: "approved" | "rejected") {
    setDecision(next);
    setComments("");
    setReviewError(null);
    setReviewOpen(true);
  }

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <Link to="/recommendations" className="inline-flex items-center gap-1 font-medium hover:text-slate-700">
          <ArrowLeft className="h-3.5 w-3.5" /> Recomendaciones
        </Link>
        <span>/</span>
        <span className="font-mono font-semibold text-slate-600">{recommendation.id.slice(0, 8)}</span>
      </div>

      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="max-w-4xl text-2xl font-bold tracking-tight text-ink-950 sm:text-3xl">
              {payload.problem || recommendation.finding_title || "Propuesta de corrección"}
            </h1>
            <RecommendationStatusBadge status={recommendation.status} />
          </div>
          <p className="mt-1.5 text-sm text-slate-500">
            {recommendation.server_name ?? "Servidor"} · {recommendation.control_code ?? "Control"} ·{" "}
            {recommendation.provider} / {recommendation.model} · {dateTime(recommendation.created_at)}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
            <span className="inline-flex items-center gap-1"><Clock3 className="h-3.5 w-3.5" /> {relativeTime(recommendation.created_at)}</span>
            <span className="inline-flex items-center gap-1"><UserCheck className="h-3.5 w-3.5" /> Generada por {recommendation.created_by_name ?? "sistema"}</span>
            <Link to={`/findings/${recommendation.finding_id}`} className="inline-flex items-center gap-1 font-semibold text-accent-700 hover:underline">
              Ver hallazgo <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {canReview && !dangerous && (
            <Button variant="secondary" icon={<XCircle className="h-4 w-4" />} onClick={() => openReview("rejected")}>
              Rechazar
            </Button>
          )}
          {canReview && (
            <Button
              variant={dangerous ? "secondary" : "primary"}
              icon={<CheckCircle2 className="h-4 w-4" />}
              disabled={dangerous}
              onClick={() => openReview("approved")}
            >
              Aprobar propuesta
            </Button>
          )}
        </div>
      </div>

      <div className="mb-5 rounded-2xl border border-cyan-200 bg-gradient-to-r from-cyan-50 to-white p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-100 text-cyan-800">
            <Ban className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-bold text-cyan-950">Ningún comando se ejecuta desde la plataforma</p>
            <p className="mt-0.5 text-[11px] leading-5 text-cyan-800/80">
              Esta es una propuesta para revisión humana. La aprobación documenta la decisión, no aplica
              cambios en el servidor. Cualquier corrección debe ejecutarse fuera de la plataforma con
              respaldo, ventana y plan de reversión.
            </p>
          </div>
        </div>
      </div>

      {dangerous && (
        <Alert tone="danger" className="mb-5" title="La propuesta contiene comandos destructivos">
          No puede aprobarse. Rechace esta propuesta y solicite una nueva. Los comandos detectados se
          muestran abajo con su motivo.
        </Alert>
      )}
      {payload.insufficient_information && (
        <Alert tone="warning" className="mb-5" title="Información insuficiente">
          El modelo indicó que no cuenta con información suficiente para proponer una corrección segura.
          No invente comandos: revise el servidor y genere una propuesta con más evidencia.
        </Alert>
      )}

      <div className="grid gap-5 xl:grid-cols-12">
        <div className="space-y-5 xl:col-span-8">
          <Card className="p-5">
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <p className="section-kicker">Problema</p>
                <p className="mt-2 text-xs leading-6 text-slate-600">{payload.problem}</p>
              </div>
              <div>
                <p className="section-kicker">Riesgo asociado</p>
                <p className="mt-2 text-xs leading-6 text-slate-600">{payload.risk}</p>
              </div>
            </div>
            <div className="mt-5 border-t border-line pt-5">
              <p className="section-kicker">Recomendación priorizada</p>
              <p className="mt-2 text-sm leading-7 text-ink-900">{payload.recommendation}</p>
            </div>
          </Card>

          <Card className="p-5">
            <SectionHeader
              title="Comandos sugeridos"
              description="Nunca se ejecutan automáticamente. Revise cada uno en un entorno de prueba."
              action={<Badge tone={dangerous ? "danger" : "neutral"}>{payload.commands.length} comando(s)</Badge>}
            />
            {payload.commands.length ? (
              <div className="mt-4 space-y-4">
                {payload.commands.map((step, index) => {
                  const isFlagged = flagged.has(step.command);
                  return (
                    <div
                      key={`${step.command}-${index}`}
                      className={clsx(
                        "overflow-hidden rounded-xl border",
                        isFlagged ? "border-red-200" : "border-line",
                      )}
                    >
                      <div className="flex items-center justify-between gap-3 border-b border-line bg-slate-50/80 px-3 py-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                          Paso {index + 1}
                        </span>
                        <CopyButton value={step.command} label="Copiar comando" />
                      </div>
                      <pre className="overflow-x-auto whitespace-pre-wrap break-words bg-ink-950 p-3.5 font-mono text-xs leading-6 text-slate-200">
                        {step.command}
                      </pre>
                      <div className="space-y-2 p-3.5">
                        <p className="text-[11px] leading-5 text-slate-600">{step.explanation}</p>
                        {step.risk && (
                          <p className="flex items-start gap-1.5 text-[10px] leading-5 text-amber-700">
                            <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" /> {step.risk}
                          </p>
                        )}
                        {isFlagged && (
                          <p className="flex items-start gap-1.5 rounded-lg bg-red-50 p-2 text-[10px] leading-5 text-red-700">
                            <ShieldAlert className="mt-0.5 h-3 w-3 shrink-0" />
                            Marcado por el validador: {recommendation.flagged_commands.find((flag) => flag.command === step.command)?.reason}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="mt-4 rounded-xl border border-dashed border-line bg-slate-50 p-5 text-center">
                <Info className="mx-auto h-5 w-5 text-slate-400" />
                <p className="mt-2 text-xs font-semibold text-slate-600">Sin comandos propuestos</p>
                <p className="mt-1 text-[11px] leading-5 text-slate-400">
                  La propuesta requiere diseño manual o más evidencia. No se deben inventar comandos.
                </p>
              </div>
            )}
          </Card>

          <div className="grid gap-5 sm:grid-cols-2">
            <Card className="p-5">
              <SectionHeader title="Requisitos previos" />
              <ul className="mt-3 space-y-2 text-[11px] leading-5 text-slate-600">
                {payload.prerequisites.length ? payload.prerequisites.map((item) => (
                  <li key={item} className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" /> {item}</li>
                )) : <li className="text-slate-400">No especificados.</li>}
              </ul>
            </Card>
            <Card className="p-5">
              <SectionHeader title="Validación posterior" />
              <ul className="mt-3 space-y-2 text-[11px] leading-5 text-slate-600">
                {payload.validation.length ? payload.validation.map((item) => (
                  <li key={item} className="flex gap-2"><RotateCcw className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent-600" /> {item}</li>
                )) : <li className="text-slate-400">No especificada.</li>}
              </ul>
            </Card>
            <Card className="p-5">
              <SectionHeader title="Plan de reversión" />
              <ul className="mt-3 space-y-2 text-[11px] leading-5 text-slate-600">
                {payload.rollback.length ? payload.rollback.map((item) => (
                  <li key={item} className="flex gap-2"><RotateCcw className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" /> {item}</li>
                )) : <li className="text-amber-600">No se propuso un procedimiento de reversión.</li>}
              </ul>
            </Card>
            <Card className="p-5">
              <SectionHeader title="Impacto" />
              <p className="mt-3 text-[11px] leading-6 text-slate-600">{payload.impact}</p>
            </Card>
          </div>
        </div>

        <div className="space-y-5 xl:col-span-4">
          <Card className="p-5">
            <SectionHeader title="Validación de seguridad" />
            <div className="mt-4 flex items-center gap-2">
              <Badge tone={validationTone(recommendation.validation_status)}>
                {recommendation.validation_status === "dangerous"
                  ? "Peligrosa"
                  : recommendation.validation_status === "warnings"
                    ? "Con advertencias"
                    : "Sin verificación automática"}
              </Badge>
              <span className="text-[10px] text-slate-400">Confianza {recommendation.confidence !== null ? percent(recommendation.confidence * 100, 0) : "—"}</span>
            </div>
            {recommendation.validation_warnings.length > 0 && (
              <ul className="mt-3 space-y-2">
                {recommendation.validation_warnings.map((warning) => (
                  <li key={warning} className="flex gap-2 rounded-lg bg-amber-50 p-2 text-[10px] leading-5 text-amber-800">
                    <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" /> {warning}
                  </li>
                ))}
              </ul>
            )}
            {!recommendation.validation_warnings.length && (
              <p className="mt-3 text-[10px] leading-5 text-slate-400">
                Sin advertencias del validador. Esto no convierte la propuesta en verificada ni segura.
              </p>
            )}
          </Card>

          <Card className="p-5">
            <SectionHeader title="Ficha de la propuesta" />
            <dl className="mt-4 space-y-3.5">
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Riesgo de interrupción</dt>
                <dd className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-ink-900">
                  <AlertTriangle className={clsx("h-3.5 w-3.5", payload.service_interruption_risk === "high" ? "text-red-500" : "text-amber-500")} />
                  {interruptionLabel[payload.service_interruption_risk] ?? payload.service_interruption_risk}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Origen</dt>
                <dd className="mt-1 text-xs">{recommendation.provider} / {recommendation.model}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Estado de revisión</dt>
                <dd className="mt-1"><RecommendationStatusBadge status={recommendation.status} /></dd>
              </div>
              <div>
                <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Revisada por</dt>
                <dd className="mt-1 text-xs">{recommendation.reviewed_by_name ?? "Pendiente de revisión humana"}</dd>
              </div>
            </dl>
            {recommendation.reviewed_at && (
              <div className="mt-4 rounded-xl border border-line bg-slate-50 p-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Comentario de revisión</p>
                <p className="mt-1 text-[11px] leading-5 text-slate-600">{recommendation.review_note ?? "—"}</p>
                <p className="mt-1 text-[10px] text-slate-400">{dateTime(recommendation.reviewed_at)}</p>
              </div>
            )}
          </Card>

          {payload.references.length > 0 && (
            <Card className="p-5">
              <SectionHeader title="Referencias" />
              <ul className="mt-3 space-y-2">
                {payload.references.map((reference) => (
                  <li key={reference}>
                    {reference.startsWith("http") ? (
                      <a
                        href={reference}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="break-all text-[11px] font-medium text-accent-700 hover:underline"
                      >
                        {reference}
                      </a>
                    ) : (
                      <span className="text-[11px] text-slate-500">{reference}</span>
                    )}
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card className="p-5">
            <SectionHeader title="Historial de revisión" />
            {recommendation.reviews.length ? (
              <div className="mt-4 space-y-4">
                {recommendation.reviews.map((review) => (
                  <div key={review.id} className="flex gap-3">
                    <span
                      className={clsx(
                        "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                        review.decision === "approved" ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600",
                      )}
                    >
                      {review.decision === "approved" ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
                    </span>
                    <div>
                      <p className="text-[11px] font-semibold text-slate-700">
                        {review.decision === "approved" ? "Aprobada" : "Rechazada"} por {review.reviewer_name ?? "usuario"}
                      </p>
                      <p className="mt-0.5 text-[10px] leading-5 text-slate-500">{review.comments}</p>
                      <p className="text-[9px] text-slate-400">{dateTime(review.created_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-[11px] leading-5 text-slate-400">
                Aún no existe una revisión humana registrada.
              </p>
            )}
          </Card>
        </div>
      </div>

      <Modal
        open={reviewOpen}
        onClose={() => setReviewOpen(false)}
        title={decision === "approved" ? "Aprobar propuesta" : "Rechazar propuesta"}
        description={
          decision === "approved"
            ? "La aprobación documenta que el plan fue revisado. No ejecuta comandos ni modifica servidores."
            : "Registre el motivo del rechazo para que el equipo pueda solicitar una nueva propuesta."
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setReviewOpen(false)}>Cancelar</Button>
            <Button
              variant={decision === "approved" ? "primary" : "danger"}
              loading={reviewMutation.isPending}
              disabled={comments.trim().length < 10}
              onClick={() => {
                setReviewError(null);
                reviewMutation.mutate();
              }}
            >
              {decision === "approved" ? "Confirmar aprobación" : "Confirmar rechazo"}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {reviewError && <Alert tone="danger">{reviewError}</Alert>}
          <Alert tone="info">
            La revisión se registra con su usuario, fecha y comentario en la bitácora. No se ejecutará
            ningún comando.
          </Alert>
          <FormField label="Comentario de revisión" required hint="Mínimo 10 caracteres.">
            <textarea
              className="textarea"
              value={comments}
              onChange={(event) => setComments(event.target.value)}
              placeholder="Explique la decisión y cualquier condición para aplicar la corrección…"
              maxLength={4000}
            />
          </FormField>
        </div>
      </Modal>
    </>
  );
}
