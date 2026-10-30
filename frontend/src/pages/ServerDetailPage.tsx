import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import {
  ArrowLeft,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Copy,
  Edit3,
  Fingerprint,
  KeyRound,
  Network,
  Play,
  Radar,
  RefreshCcw,
  Server as ServerIcon,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ServerFormModal } from "../components/ServerFormModal";
import { StartAuditModal } from "../components/StartAuditModal";
import {
  Alert,
  Badge,
  Button,
  Card,
  ConfirmModal,
  CopyButton,
  EmptyState,
  ErrorState,
  FindingStatusBadge,
  FormField,
  KeyValue,
  Modal,
  PageLoader,
  RunStatusBadge,
  ScoreRing,
  SectionHeader,
  ServerStatusBadge,
  SeverityBadge,
  TableSkeleton,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, auditsApi, findingsApi, serversApi } from "../lib/api";
import {
  dateTime,
  environmentLabel,
  percent,
  relativeTime,
  scoreTone,
  shortDate,
  truncate,
} from "../lib/format";

export function ServerDetailPage() {
  const { serverId = "" } = useParams();
  const { hasPermission, hasAnyPermission } = useAuth();
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [editOpen, setEditOpen] = useState(false);
  const [auditOpen, setAuditOpen] = useState(false);
  const [authorizeOpen, setAuthorizeOpen] = useState(false);
  const [credentialOpen, setCredentialOpen] = useState(false);
  const [allowPrivate, setAllowPrivate] = useState(false);
  const [secret, setSecret] = useState("");
  const [dialogError, setDialogError] = useState<string | null>(null);

  const serverQuery = useQuery({
    queryKey: ["server", serverId],
    queryFn: () => serversApi.get(serverId),
    enabled: Boolean(serverId),
  });
  const auditsQuery = useQuery({
    queryKey: ["audits", "server", serverId],
    queryFn: () => auditsApi.list({ server_id: serverId, page_size: 6 }),
    enabled: Boolean(serverId),
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      return items.some((run) => run.status === "queued" || run.status === "running") ? 2500 : false;
    },
  });
  const findingsQuery = useQuery({
    queryKey: ["findings", "server", serverId],
    queryFn: () => findingsApi.list({ server_id: serverId, page_size: 6 }),
    enabled: Boolean(serverId),
  });

  const testMutation = useMutation({
    mutationFn: () => serversApi.testConnection(serverId),
    onSuccess: (result) => {
      notify({
        tone: result.reachable ? "success" : "error",
        title: result.reachable ? "Conexión verificada" : "No se pudo conectar",
        message: result.message,
      });
      void queryClient.invalidateQueries({ queryKey: ["server", serverId] });
    },
    onError: (error) => {
      notify({
        tone: "error",
        title: "Prueba de conexión fallida",
        message: error instanceof ApiError ? error.message : "Error inesperado.",
      });
    },
  });

  const authorizeMutation = useMutation({
    mutationFn: (confirmed: boolean) =>
      serversApi.authorize(serverId, {
        confirmed,
        allow_private_target: allowPrivate,
        comment: confirmed ? "Autorización confirmada desde la consola." : "Autorización revocada.",
      }),
    onSuccess: (_, confirmed) => {
      notify({
        tone: confirmed ? "success" : "info",
        title: confirmed ? "Servidor autorizado" : "Autorización revocada",
        message: confirmed
          ? "Ya se pueden ejecutar auditorías sobre este servidor."
          : "Las auditorías quedarán bloqueadas hasta una nueva autorización.",
      });
      setAuthorizeOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["server", serverId] });
    },
    onError: (error) =>
      setDialogError(error instanceof ApiError ? error.message : "No fue posible actualizar la autorización."),
  });

  const credentialMutation = useMutation({
    mutationFn: () => serversApi.setCredential(serverId, secret),
    onSuccess: () => {
      notify({ tone: "success", title: "Credencial actualizada", message: "El secreto fue cifrado y no se volverá a mostrar." });
      setCredentialOpen(false);
      setSecret("");
      void queryClient.invalidateQueries({ queryKey: ["server", serverId] });
    },
    onError: (error) =>
      setDialogError(error instanceof ApiError ? error.message : "No fue posible actualizar la credencial."),
  });

  if (serverQuery.isLoading) return <PageLoader label="Cargando servidor…" />;
  if (serverQuery.isError || !serverQuery.data) {
    return (
      <ErrorState
        title="Servidor no disponible"
        message="No existe o no pertenece a su organización."
        onRetry={() => void serverQuery.refetch()}
      />
    );
  }
  const server = serverQuery.data;
  const latestRun = auditsQuery.data?.items[0];
  const tone = scoreTone(server.last_score);

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <Link to="/servers" className="inline-flex items-center gap-1 font-medium hover:text-slate-700">
          <ArrowLeft className="h-3.5 w-3.5" /> Servidores
        </Link>
        <span>/</span>
        <span className="font-semibold text-slate-600">{server.name}</span>
      </div>

      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div
            className={clsx(
              "flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border",
              server.is_simulated
                ? "border-amber-200 bg-amber-50 text-amber-600"
                : "border-line bg-white text-slate-500 shadow-card",
            )}
          >
            <ServerIcon className="h-6 w-6" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="truncate text-2xl font-bold tracking-tight text-ink-950 sm:text-3xl">{server.name}</h1>
              <ServerStatusBadge status={server.status} />
              {server.is_simulated && <Badge tone="warning">Simulado</Badge>}
              {!server.authorization_confirmed && <Badge tone="danger">Sin autorización</Badge>}
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {server.hostname} · <span className="font-mono text-xs">{server.ip_address}:{server.port}</span> ·{" "}
              {server.os_family} {server.os_version}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
              <span className="inline-flex items-center gap-1">
                <CalendarClock className="h-3.5 w-3.5" />
                Última auditoría: {server.last_audit_at ? dateTime(server.last_audit_at) : "nunca"}
              </span>
              <span className="inline-flex items-center gap-1">
                <Radar className="h-3.5 w-3.5" />
                {server.total_audits} ejecuciones
              </span>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {hasAnyPermission("audits:execute", "servers:manage") && (
            <Button
              variant="secondary"
              icon={<Wifi className="h-4 w-4" />}
              loading={testMutation.isPending}
              onClick={() => testMutation.mutate()}
            >
              Probar conexión
            </Button>
          )}
          {hasPermission("audits:execute") && (
            <Button icon={<Play className="h-4 w-4" />} onClick={() => setAuditOpen(true)}>
              Auditar ahora
            </Button>
          )}
          {hasPermission("servers:manage") && (
            <Button variant="secondary" icon={<Edit3 className="h-4 w-4" />} onClick={() => setEditOpen(true)}>
              Editar
            </Button>
          )}
        </div>
      </div>

      {server.is_simulated && (
        <Alert tone="warning" className="mb-5" title="Datos simulados">
          Este servidor usa el conector de pruebas. Los resultados no provienen de infraestructura real
          y se identifican como simulados en dashboard, auditorías y reportes.
        </Alert>
      )}
      {!server.authorization_confirmed && !server.is_simulated && (
        <Alert tone="warning" className="mb-5" title="Autorización pendiente">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span>Las auditorías están bloqueadas hasta confirmar la autorización explícita.</span>
            {hasPermission("servers:manage") && (
              <Button size="sm" onClick={() => setAuthorizeOpen(true)}>
                Autorizar servidor
              </Button>
            )}
          </div>
        </Alert>
      )}
      {server.is_active === false && (
        <Alert tone="danger" className="mb-5" title="Servidor desactivado">
          El servidor no puede auditarse mientras permanezca inactivo.
        </Alert>
      )}

      <div className="grid gap-5 xl:grid-cols-12">
        <div className="space-y-5 xl:col-span-8">
          <Card className="p-5">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="section-kicker">Última evaluación</p>
                <h2 className="mt-1 text-lg font-bold text-ink-950">
                  {latestRun ? latestRun.profile_name : "Sin auditorías"}
                </h2>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {latestRun
                    ? `Ejecutada ${relativeTime(latestRun.created_at)} · ${latestRun.passed_count} aprobados, ${latestRun.failed_count} incumplidos`
                    : "Aún no se ha ejecutado una auditoría sobre este servidor."}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {latestRun ? (
                    <>
                      <RunStatusBadge status={latestRun.status} />
                      {latestRun.is_simulated && <Badge tone="warning">Simulado</Badge>}
                    </>
                  ) : (
                    <Badge tone="neutral">Pendiente</Badge>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-5">
                <ScoreRing score={server.last_score} size={132} />
                <div className="space-y-2 text-xs">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Hallazgos activos</p>
                    <p className="mt-0.5 text-lg font-bold text-ink-900">{server.active_findings}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Críticos / altos</p>
                    <p className="mt-0.5 font-semibold text-red-600">
                      {(server.open_findings_by_severity?.critical ?? 0) + (server.open_findings_by_severity?.high ?? 0)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            {latestRun && (
              <div className="mt-5 border-t border-line pt-4">
                <div className="grid gap-4 sm:grid-cols-4">
                  {[
                    ["Aprobados", latestRun.passed_count],
                    ["Incumplidos", latestRun.failed_count],
                    ["No evaluados", latestRun.not_evaluated_count],
                    ["No aplica", latestRun.not_applicable_count],
                  ].map(([label, value]) => (
                    <div key={String(label)}>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</p>
                      <p className="mt-0.5 text-sm font-bold tabular-nums text-ink-900">{value}</p>
                    </div>
                  ))}
                </div>
                <Link
                  to={`/audits/${latestRun.id}`}
                  className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-accent-700 hover:underline"
                >
                  Ver evidencia completa <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            )}
          </Card>

          <Card className="overflow-hidden">
            <div className="p-5 pb-2">
              <SectionHeader
                title="Historial de auditorías"
                description="Resultados guardados con su perfil y versión del benchmark."
                action={
                  <button
                    className="text-[11px] font-semibold text-accent-700 hover:underline"
                    onClick={() => void auditsQuery.refetch()}
                  >
                    Actualizar
                  </button>
                }
              />
            </div>
            {auditsQuery.isLoading ? (
              <div className="p-4">
                <TableSkeleton rows={3} cols={4} />
              </div>
            ) : auditsQuery.data?.items.length ? (
              <div className="overflow-x-auto">
                <table className="data-table min-w-[660px]">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Estado</th>
                      <th>Cumplimiento</th>
                      <th>Fallos</th>
                      <th>Perfil</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {auditsQuery.data.items.map((run) => (
                      <tr key={run.id} className="clickable" onClick={() => navigate(`/audits/${run.id}`)}>
                        <td className="whitespace-nowrap text-xs">{dateTime(run.created_at)}</td>
                        <td><RunStatusBadge status={run.status} /></td>
                        <td>
                          <span
                            className={clsx(
                              "text-sm font-bold tabular-nums",
                              scoreTone(run.score) === "good" && "text-emerald-600",
                              scoreTone(run.score) === "warn" && "text-amber-600",
                              scoreTone(run.score) === "bad" && "text-red-600",
                            )}
                          >
                            {percent(run.score)}
                          </span>
                        </td>
                        <td>{run.failed_count}</td>
                        <td className="max-w-[200px] truncate text-xs">{run.profile_name}</td>
                        <td><ChevronRight className="h-4 w-4 text-slate-300" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState icon={<Radar className="h-5 w-5" />} title="Sin historial" description="Aún no hay ejecuciones para este servidor." />
            )}
          </Card>

          <Card className="overflow-hidden">
            <div className="flex items-center justify-between p-5 pb-2">
              <SectionHeader title="Hallazgos activos" description="Incumplimientos con seguimiento abierto." />
              <Link to={`/findings?server_id=${server.id}`} className="text-[11px] font-semibold text-accent-700 hover:underline">
                Ver todos
              </Link>
            </div>
            {findingsQuery.isLoading ? (
              <div className="p-4"><TableSkeleton rows={3} cols={4} /></div>
            ) : findingsQuery.data?.items.length ? (
              <div className="overflow-x-auto">
                <table className="data-table min-w-[660px]">
                  <thead>
                    <tr>
                      <th>Hallazgo</th>
                      <th>Severidad</th>
                      <th>Estado</th>
                      <th>Vence</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {findingsQuery.data.items.map((finding) => (
                      <tr key={finding.id} className="clickable" onClick={() => navigate(`/findings/${finding.id}`)}>
                        <td>
                          <p className="max-w-[320px] truncate text-xs font-semibold text-ink-900">{finding.title}</p>
                          <p className="mt-0.5 text-[10px] text-slate-400">{finding.cis_reference ?? finding.control_code}</p>
                        </td>
                        <td><SeverityBadge severity={finding.severity} /></td>
                        <td><FindingStatusBadge status={finding.status} /></td>
                        <td className="text-xs">{finding.due_date ? shortDate(finding.due_date) : "—"}</td>
                        <td><ChevronRight className="h-4 w-4 text-slate-300" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState icon={<CheckCircle2 className="h-5 w-5" />} title="Sin hallazgos activos" description="El servidor no tiene incumplimientos abiertos." />
            )}
          </Card>

          {server.notes && (
            <Card className="p-5">
              <SectionHeader title="Notas del servidor" />
              <p className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-600">{server.notes}</p>
            </Card>
          )}
        </div>

        <div className="space-y-5 xl:col-span-4">
          <Card className="p-5">
            <SectionHeader title="Ficha técnica" />
            <dl className="mt-4 grid grid-cols-2 gap-4">
              <KeyValue label="Entorno">{environmentLabel[server.environment]}</KeyValue>
              <KeyValue label="Área">{server.owner_area ?? "—"}</KeyValue>
              <KeyValue label="Método">{server.connection_method === "ssh" ? "SSH" : "Simulado"}</KeyValue>
              <KeyValue label="Autenticación">{server.auth_method === "key" ? "Clave privada" : "Contraseña"}</KeyValue>
              <KeyValue label="Usuario">{server.username ?? "—"}</KeyValue>
              <KeyValue label="Perfil">{server.default_profile_name ?? "—"}</KeyValue>
              <KeyValue label="Creado">{shortDate(server.created_at)}</KeyValue>
              <KeyValue label="Actualizado">{shortDate(server.updated_at)}</KeyValue>
            </dl>
            {server.host_key_fingerprint && (
              <div className="mt-4 rounded-xl border border-line bg-slate-50/60 p-3">
                <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  <Fingerprint className="h-3.5 w-3.5" /> Huella SSH fijada
                </p>
                <p className="mt-1 break-all font-mono text-[10px] leading-5 text-slate-600">{server.host_key_fingerprint}</p>
                <div className="mt-2"><CopyButton value={server.host_key_fingerprint} /></div>
              </div>
            )}
          </Card>

          <Card className="p-5">
            <SectionHeader title="Autorización" />
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between gap-3 rounded-xl border border-line p-3">
                <div className="flex items-center gap-2.5">
                  {server.authorization_confirmed ? (
                    <ShieldCheck className="h-5 w-5 text-emerald-600" />
                  ) : (
                    <ShieldOff className="h-5 w-5 text-red-500" />
                  )}
                  <div>
                    <p className="text-xs font-semibold text-ink-900">
                      {server.authorization_confirmed ? "Autorizado" : "No autorizado"}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {server.authorized_at ? dateTime(server.authorized_at) : "Sin confirmación"}
                    </p>
                  </div>
                </div>
                {hasPermission("servers:manage") && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setAllowPrivate(server.allow_private_target);
                      setDialogError(null);
                      setAuthorizeOpen(true);
                    }}
                  >
                    {server.authorization_confirmed ? "Gestionar" : "Autorizar"}
                  </Button>
                )}
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl border border-line p-3">
                <div className="flex items-center gap-2.5">
                  <KeyRound className="h-5 w-5 text-slate-500" />
                  <div>
                    <p className="text-xs font-semibold text-ink-900">Credencial SSH</p>
                    <p className="text-[10px] text-slate-400">
                      {server.connection_method === "simulated"
                        ? "No aplica: conector simulado"
                        : server.credential_configured
                          ? "Cifrada y configurada"
                          : "No configurada"}
                    </p>
                  </div>
                </div>
                {hasPermission("servers:manage") && server.connection_method === "ssh" && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSecret("");
                      setDialogError(null);
                      setCredentialOpen(true);
                    }}
                  >
                    Actualizar
                  </Button>
                )}
              </div>
              <div className="flex items-center gap-2.5 rounded-xl border border-line p-3">
                {server.status === "online" ? (
                  <Wifi className="h-5 w-5 text-emerald-600" />
                ) : (
                  <WifiOff className="h-5 w-5 text-slate-400" />
                )}
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-ink-900">Conectividad</p>
                  <p className="truncate text-[10px] text-slate-400" title={server.connectivity_status ?? undefined}>
                    {server.connectivity_status ?? "Aún no comprobada"}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <SectionHeader title="Alcance de evaluación" />
            <div className="mt-3 space-y-2.5 text-[11px] leading-5 text-slate-500">
              <p className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" /> Comandos de solo lectura definidos en el motor.</p>
              <p className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" /> Identidad del host validada por huella SHA256.</p>
              <p className="flex gap-2"><AlertTriangleIcon /> Los resultados no son una certificación CIS.</p>
              <p className="flex gap-2"><Clock3 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" /> Límite de ejecución y salida acotada por control.</p>
            </div>
          </Card>
        </div>
      </div>

      <ServerFormModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        server={server}
        onSaved={() => {
          void queryClient.invalidateQueries({ queryKey: ["server", serverId] });
          void queryClient.invalidateQueries({ queryKey: ["servers"] });
        }}
      />
      <StartAuditModal open={auditOpen} onClose={() => setAuditOpen(false)} />

      <Modal
        open={authorizeOpen}
        onClose={() => setAuthorizeOpen(false)}
        title={server.authorization_confirmed ? "Gestionar autorización" : "Autorizar servidor"}
        description="La autorización debe ser explícita y verificable. Quedará registrada en la bitácora."
        footer={
          <>
            <Button variant="secondary" onClick={() => setAuthorizeOpen(false)}>Cancelar</Button>
            {server.authorization_confirmed ? (
              <Button
                variant="danger"
                loading={authorizeMutation.isPending}
                onClick={() => authorizeMutation.mutate(false)}
              >
                Revocar autorización
              </Button>
            ) : (
              <Button
                loading={authorizeMutation.isPending}
                disabled={!server.is_simulated && !server.credential_configured}
                onClick={() => authorizeMutation.mutate(true)}
              >
                Confirmar autorización
              </Button>
            )}
          </>
        }
      >
        <div className="space-y-4">
          {dialogError && <Alert tone="danger">{dialogError}</Alert>}
          <Alert tone="info">
            El servidor solo se auditará mediante comprobaciones de lectura. No se aplicarán cambios
            automáticos de configuración.
          </Alert>
          {!server.authorization_confirmed && !server.is_simulated && !server.credential_configured && (
            <Alert tone="warning">Configure la credencial SSH antes de autorizar el servidor.</Alert>
          )}
          <label className="flex items-start gap-2.5 text-xs leading-5 text-slate-600">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-accent-600"
              checked={allowPrivate}
              onChange={(event) => setAllowPrivate(event.target.checked)}
            />
            <span>Autorizo un objetivo en red privada (requiere habilitación global del backend).</span>
          </label>
        </div>
      </Modal>

      <Modal
        open={credentialOpen}
        onClose={() => setCredentialOpen(false)}
        title="Actualizar credencial SSH"
        description="El secreto se cifra antes de guardarse y nunca se devuelve por la API."
        footer={
          <>
            <Button variant="secondary" onClick={() => setCredentialOpen(false)}>Cancelar</Button>
            <Button
              loading={credentialMutation.isPending}
              disabled={secret.trim().length < 8}
              onClick={() => {
                setDialogError(null);
                credentialMutation.mutate();
              }}
            >
              Guardar credencial
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {dialogError && <Alert tone="danger">{dialogError}</Alert>}
          <FormField
            label={server.auth_method === "key" ? "Nueva clave privada" : "Nueva contraseña SSH"}
            required
            hint="No se muestra ni se registra en logs."
          >
            {server.auth_method === "key" ? (
              <textarea
                className="textarea font-mono text-xs"
                value={secret}
                onChange={(event) => setSecret(event.target.value)}
                placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                spellCheck={false}
                autoComplete="off"
              />
            ) : (
              <input
                type="password"
                className="input"
                value={secret}
                onChange={(event) => setSecret(event.target.value)}
                autoComplete="new-password"
              />
            )}
          </FormField>
          <Alert tone="warning">
            Tras actualizar la credencial, pruebe la conexión antes de ejecutar una auditoría.
          </Alert>
        </div>
      </Modal>
    </>
  );
}

function AlertTriangleIcon() {
  return <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />;
}
