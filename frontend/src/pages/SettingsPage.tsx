import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  CircleSlash,
  Clock3,
  Cpu,
  Database,
  KeyRound,
  LockKeyhole,
  Plus,
  ServerCog,
  ShieldCheck,
  Trash2,
  Workflow,
} from "lucide-react";
import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  CopyButton,
  EmptyState,
  ErrorState,
  FormField,
  Input,
  Modal,
  PageLoader,
  PageHeader,
  SectionHeader,
} from "../components/ui";
import { useToast } from "../context/Toast";
import { ApiError, settingsApi } from "../lib/api";
import { dateTime, relativeTime } from "../lib/format";
import type { ApiTokenCreated } from "../types";

export function SettingsPage() {
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [tokenOpen, setTokenOpen] = useState(false);
  const [createdToken, setCreatedToken] = useState<ApiTokenCreated | null>(null);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string[]>(["automation:execute"]);
  const [days, setDays] = useState(365);
  const [error, setError] = useState<string | null>(null);

  const systemQuery = useQuery({ queryKey: ["settings", "system"], queryFn: settingsApi.get });
  const tokensQuery = useQuery({ queryKey: ["settings", "tokens"], queryFn: settingsApi.tokens });

  const createMutation = useMutation({
    mutationFn: () => settingsApi.createToken({ name: name.trim(), scopes, expires_in_days: days }),
    onSuccess: (token) => {
      setTokenOpen(false);
      setCreatedToken(token);
      setName("");
      void queryClient.invalidateQueries({ queryKey: ["settings", "tokens"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "No fue posible crear el token."),
  });
  const revokeMutation = useMutation({
    mutationFn: (id: string) => settingsApi.revokeToken(id),
    onSuccess: () => {
      notify({ tone: "success", title: "Token revocado" });
      void queryClient.invalidateQueries({ queryKey: ["settings", "tokens"] });
    },
    onError: (err) => notify({ tone: "error", title: "No se pudo revocar", message: err instanceof ApiError ? err.message : undefined }),
  });

  if (systemQuery.isLoading) return <PageLoader label="Cargando configuración…" />;
  if (systemQuery.isError || !systemQuery.data) {
    return <ErrorState message="No se pudo consultar el estado del sistema." onRetry={() => void systemQuery.refetch()} />;
  }
  const system = systemQuery.data;
  const aiAvailable = system.ai.enabled && system.ai.available;

  return (
    <>
      <PageHeader
        kicker="Operación de la plataforma"
        title="Configuración"
        description="Estado de integraciones, tokens de automatización y controles de seguridad del despliegue."
      />

      <div className="grid gap-5 xl:grid-cols-12">
        <div className="space-y-5 xl:col-span-7">
          <Card className="p-5">
            <SectionHeader title="Estado del sistema" description="Datos leídos de la configuración del backend." />
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-line p-4">
                <div className="flex items-center justify-between">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500"><Cpu className="h-4 w-4" /></span>
                  <Badge tone="neutral">{system.environment}</Badge>
                </div>
                <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">Producto</p>
                <p className="mt-0.5 text-sm font-bold text-ink-900">{system.product}</p>
                <p className="text-[10px] text-slate-400">Versión {system.version}</p>
              </div>
              <div className="rounded-xl border border-line p-4">
                <div className="flex items-center justify-between">
                  <span className={clsx("flex h-8 w-8 items-center justify-center rounded-lg", aiAvailable ? "bg-violet-50 text-violet-600" : "bg-slate-100 text-slate-500")}><Bot className="h-4 w-4" /></span>
                  <Badge tone={aiAvailable ? "success" : "neutral"} dot>{aiAvailable ? "Disponible" : "No disponible"}</Badge>
                </div>
                <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">Asistente IA</p>
                <p className="mt-0.5 text-sm font-bold text-ink-900">{system.ai.model}</p>
                <p className="text-[10px] text-slate-400">
                  {system.ai.enabled ? (system.ai.available ? "Ollama responde" : "Ollama sin conexión") : "Deshabilitado por configuración"}
                </p>
              </div>
              <div className="rounded-xl border border-line p-4">
                <div className="flex items-center justify-between">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-50 text-accent-700"><ServerCog className="h-4 w-4" /></span>
                  <Badge tone={system.simulated_connector_enabled ? "warning" : "success"}>{system.simulated_connector_enabled ? "Activo" : "Desactivado"}</Badge>
                </div>
                <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">Conector simulado</p>
                <p className="mt-0.5 text-sm font-bold text-ink-900">{system.simulated_connector_enabled ? "Modo pruebas" : "Solo SSH real"}</p>
                <p className="text-[10px] text-slate-400">No debe habilitarse en producción.</p>
              </div>
              <div className="rounded-xl border border-line p-4">
                <div className="flex items-center justify-between">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500"><LockKeyhole className="h-4 w-4" /></span>
                  <Badge tone={system.private_targets_enabled ? "warning" : "neutral"}>{system.private_targets_enabled ? "Habilitado" : "Bloqueado"}</Badge>
                </div>
                <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">Objetivos privados</p>
                <p className="mt-0.5 text-sm font-bold text-ink-900">{system.private_targets_enabled ? "Permitidos con autorización" : "Requieren habilitación"}</p>
                <p className="text-[10px] text-slate-400">Loopback y metadatos siempre bloqueados.</p>
              </div>
            </div>
            <div className="mt-4 flex items-start gap-3 rounded-xl border border-line bg-slate-50/60 p-3.5 text-[10px] leading-5 text-slate-500">
              <Database className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              Almacenamiento de reportes: <span className="break-all font-mono">{system.reports_storage}</span> · Ejecuciones simultáneas: {system.audit_max_concurrent_runs}
            </div>
          </Card>

          <Card className="p-5">
            <SectionHeader
              title="Tokens de automatización"
              description="Usados por n8n con alcance limitado. El token completo se muestra una única vez."
              action={<Button size="sm" icon={<Plus className="h-4 w-4" />} onClick={() => { setError(null); setTokenOpen(true); }}>Crear token</Button>}
            />
            {tokensQuery.isLoading ? (
              <p className="mt-4 text-xs text-slate-400">Cargando tokens…</p>
            ) : tokensQuery.data?.length ? (
              <div className="mt-4 space-y-3">
                {tokensQuery.data.map((token) => (
                  <div key={token.id} className="rounded-xl border border-line p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="flex items-start gap-2.5">
                        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500"><KeyRound className="h-4 w-4" /></span>
                        <div>
                          <p className="text-xs font-bold text-ink-900">{token.name}</p>
                          <p className="font-mono text-[10px] text-slate-400">{token.token_prefix}••••••••</p>
                          <div className="mt-1.5 flex flex-wrap gap-1">
                            {token.scopes.map((scope) => <Badge key={scope} tone="neutral">{scope}</Badge>)}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge tone={token.revoked_at ? "danger" : "success"}>{token.revoked_at ? "Revocado" : "Activo"}</Badge>
                        {!token.revoked_at && (
                          <Button
                            variant="secondary"
                            size="sm"
                            icon={<Trash2 className="h-3.5 w-3.5" />}
                            onClick={() => {
                              if (window.confirm("¿Revocar este token? n8n dejará de autenticarse con él.")) revokeMutation.mutate(token.id);
                            }}
                          >
                            Revocar
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-4 border-t border-line pt-2.5 text-[10px] text-slate-400">
                      <span>Creado: {dateTime(token.created_at)}</span>
                      <span>Expira: {dateTime(token.expires_at)}</span>
                      <span>Último uso: {token.last_used_at ? relativeTime(token.last_used_at) : "nunca"}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState icon={<KeyRound className="h-5 w-5" />} title="Sin tokens" description="Cree un token para conectar n8n mediante endpoints autenticados." />
            )}
          </Card>
        </div>

        <div className="space-y-5 xl:col-span-5">
          <Card className="p-5">
            <SectionHeader title="Postura de seguridad" />
            <div className="mt-4 space-y-3">
              {[
                { icon: <ShieldCheck className="h-4 w-4" />, title: "RBAC en backend", text: "Cada endpoint verifica permisos y organización." },
                { icon: <LockKeyhole className="h-4 w-4" />, title: "Credenciales cifradas", text: "Fernet con clave externa; nunca se devuelven por API." },
                { icon: <CircleSlash className="h-4 w-4" />, title: "Solo lectura", text: "No existe ejecución de correcciones ni shells interactivas." },
                { icon: <Clock3 className="h-4 w-4" />, title: "Bitácora append-only", text: "Trigger en PostgreSQL contra update/delete." },
              ].map((item) => (
                <div key={item.title} className="flex items-start gap-2.5">
                  <span className="mt-0.5 text-accent-600">{item.icon}</span>
                  <div>
                    <p className="text-xs font-semibold text-ink-900">{item.title}</p>
                    <p className="mt-0.5 text-[10px] leading-5 text-slate-500">{item.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="border-amber-200 bg-amber-50/50 p-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
              <div>
                <p className="text-xs font-bold text-amber-950">Checklist para producción</p>
                <ul className="mt-2 space-y-1.5 text-[10px] leading-5 text-amber-900/80">
                  <li>• HTTPS y cookies <code className="font-mono">Secure</code>.</li>
                  <li>• Conector simulado desactivado.</li>
                  <li>• Backups de PostgreSQL y de la clave Fernet.</li>
                  <li>• Ollama aislado en red interna.</li>
                  <li>• Revisión de AUDIT_ALLOWED_CIDRS.</li>
                </ul>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <SectionHeader title="Limitaciones" />
            <p className="mt-3 text-[11px] leading-6 text-slate-500">
              La plataforma evalúa controles de configuración, no vulnerabilidades de aplicación. Un score
              alto no certifica el servidor ni reemplaza pruebas de penetración, gestión de parches o
              revisión de arquitectura.
            </p>
          </Card>
        </div>
      </div>

      <Modal
        open={tokenOpen}
        onClose={() => setTokenOpen(false)}
        title="Crear token de automatización"
        description="El token se muestra una sola vez. Guárdelo en el gestor de credenciales de n8n."
        footer={
          <>
            <Button variant="secondary" onClick={() => setTokenOpen(false)}>Cancelar</Button>
            <Button
              loading={createMutation.isPending}
              disabled={!name.trim() || scopes.length === 0}
              onClick={() => { setError(null); createMutation.mutate(); }}
            >
              Generar token
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {error && <Alert tone="danger">{error}</Alert>}
          <FormField label="Nombre" required hint="Por ejemplo: n8n producción.">
            <Input value={name} onChange={(event) => setName(event.target.value)} maxLength={150} />
          </FormField>
          <div>
            <span className="label">Alcances</span>
            <div className="space-y-2">
              {[
                ["automation:execute", "Ejecutar auditorías programadas y detectar hallazgos persistentes"],
                ["automation:recommendations", "Solicitar propuestas de IA para hallazgos sin propuesta"],
                ["automation:reports", "Generar reportes ejecutivos por lote"],
              ].map(([scope, description]) => (
                <label key={scope} className={clsx("flex cursor-pointer items-start gap-2 rounded-xl border p-3 text-xs transition", scopes.includes(scope) ? "border-accent-400 bg-cyan-50/60" : "border-line hover:bg-slate-50")}>
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-accent-600"
                    checked={scopes.includes(scope)}
                    onChange={(event) => setScopes((current) => event.target.checked ? [...current, scope] : current.filter((item) => item !== scope))}
                  />
                  <span>
                    <span className="block font-mono text-[10px] font-semibold text-ink-900">{scope}</span>
                    <span className="text-[10px] text-slate-400">{description}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
          <FormField label="Expiración" required>
            <select className="select" value={days} onChange={(event) => setDays(Number(event.target.value))}>
              <option value={30}>30 días</option>
              <option value={90}>90 días</option>
              <option value={365}>1 año</option>
              <option value={730}>2 años</option>
            </select>
          </FormField>
          <Alert tone="warning">
            El token tiene acceso acotado a automatización. No puede administrar usuarios ni leer credenciales.
          </Alert>
        </div>
      </Modal>

      <Modal
        open={Boolean(createdToken)}
        onClose={() => setCreatedToken(null)}
        title="Token generado"
        description="Guárdelo ahora. No se volverá a mostrar."
        footer={<Button onClick={() => setCreatedToken(null)}>He guardado el token</Button>}
      >
        {createdToken && (
          <div className="space-y-4">
            <Alert tone="warning" title="Única visualización">
              Si pierde este token, deberá revocarlo y crear uno nuevo.
            </Alert>
            <div className="rounded-xl border border-line bg-slate-50 p-3">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Token</p>
              <p className="mt-1 break-all font-mono text-[11px] leading-5 text-slate-700">{createdToken.token}</p>
              <div className="mt-2"><CopyButton value={createdToken.token} label="Copiar token" /></div>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <Workflow className="h-3.5 w-3.5" />
              Configure el header <code className="font-mono">X-API-Key</code> en n8n.
            </div>
          </div>
        )}
      </Modal>
    </>
  );
}
