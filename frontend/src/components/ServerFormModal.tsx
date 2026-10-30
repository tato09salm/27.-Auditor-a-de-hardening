import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, KeyRound, Lock, Server as ServerIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useToast } from "../context/Toast";
import { ApiError, profilesApi, serversApi } from "../lib/api";
import type { Profile, Server } from "../types";
import { Alert, Button, FormField, Input, Modal } from "./ui";

interface FormState {
  name: string;
  hostname: string;
  ip_address: string;
  os_family: string;
  os_version: string;
  environment: string;
  owner_area: string;
  connection_method: "ssh" | "simulated";
  port: string;
  username: string;
  auth_method: "key" | "password";
  host_key_fingerprint: string;
  default_profile_id: string;
  authorization_confirmed: boolean;
  allow_private_target: boolean;
  notes: string;
  secret: string;
  is_active: boolean;
}

const emptyForm: FormState = {
  name: "",
  hostname: "",
  ip_address: "",
  os_family: "ubuntu",
  os_version: "22.04",
  environment: "production",
  owner_area: "",
  connection_method: "ssh",
  port: "22",
  username: "",
  auth_method: "key",
  host_key_fingerprint: "",
  default_profile_id: "",
  authorization_confirmed: false,
  allow_private_target: false,
  notes: "",
  secret: "",
  is_active: true,
};

export function ServerFormModal({
  open,
  onClose,
  server,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  server?: Server | null;
  onSaved?: (server: Server) => void;
}) {
  const { notify } = useToast();
  const editing = Boolean(server);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const profilesQuery = useQuery({
    queryKey: ["profiles"],
    queryFn: profilesApi.list,
    enabled: open,
  });
  const profiles: Profile[] = profilesQuery.data ?? [];

  useEffect(() => {
    if (!open) return;
    setError(null);
    setFieldErrors({});
    if (server) {
      setForm({
        name: server.name,
        hostname: server.hostname,
        ip_address: server.ip_address,
        os_family: server.os_family,
        os_version: server.os_version,
        environment: server.environment,
        owner_area: server.owner_area ?? "",
        connection_method: server.connection_method,
        port: String(server.port),
        username: server.username ?? "",
        auth_method: server.auth_method,
        host_key_fingerprint: server.host_key_fingerprint ?? "",
        default_profile_id: server.default_profile_id ?? "",
        authorization_confirmed: server.authorization_confirmed,
        allow_private_target: server.allow_private_target,
        notes: server.notes ?? "",
        secret: "",
        is_active: server.is_active,
      });
    } else {
      setForm({
        ...emptyForm,
        default_profile_id: profilesQuery.data?.[0]?.id ?? "",
      });
    }
  }, [open, server]);

  useEffect(() => {
    if (!editing && open && !form.default_profile_id && profiles.length) {
      setForm((current) => ({ ...current, default_profile_id: profiles[0].id }));
    }
  }, [editing, open, profiles, form.default_profile_id]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  const isSsh = form.connection_method === "ssh";

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (form.name.trim().length < 2) errors.name = "Ingrese un nombre de al menos 2 caracteres.";
    if (!form.hostname.trim()) errors.hostname = "El hostname es obligatorio.";
    if (!form.ip_address.trim()) errors.ip_address = "La dirección IP es obligatoria.";
    if (!form.default_profile_id) errors.default_profile_id = "Seleccione un perfil.";
    if (isSsh) {
      if (!form.username.trim()) errors.username = "El usuario técnico es obligatorio.";
      if (!/^SHA256:[A-Za-z0-9+/]{43}=?$/.test(form.host_key_fingerprint.trim()))
        errors.host_key_fingerprint = "Use una huella SHA256 válida (SHA256:…).";
      if (!editing && form.secret.trim().length < 8)
        errors.secret = "Registre la contraseña o clave privada (mínimo 8 caracteres).";
    }
    if (!editing && !form.authorization_confirmed)
      errors.authorization_confirmed = "Debe confirmar la autorización explícita.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  const mutation = useMutation({
    mutationFn: async () => {
      if (editing && server) {
        const payload: Record<string, unknown> = {};
        if (form.name.trim() !== server.name) payload.name = form.name.trim();
        if (form.hostname.trim() !== server.hostname) payload.hostname = form.hostname.trim();
        if (form.ip_address.trim() !== server.ip_address) payload.ip_address = form.ip_address.trim();
        if (form.os_version.trim() !== server.os_version) payload.os_version = form.os_version.trim();
        if (form.environment !== server.environment) payload.environment = form.environment;
        if ((form.owner_area.trim() || null) !== server.owner_area)
          payload.owner_area = form.owner_area.trim() || null;
        if (Number(form.port) !== server.port) payload.port = Number(form.port);
        if (form.default_profile_id !== server.default_profile_id)
          payload.default_profile_id = form.default_profile_id || null;
        if ((form.notes.trim() || null) !== server.notes) payload.notes = form.notes.trim() || null;
        if (form.allow_private_target !== server.allow_private_target)
          payload.allow_private_target = form.allow_private_target;
        if (form.is_active !== server.is_active) payload.is_active = form.is_active;
        return serversApi.update(server.id, payload);
      }
      const payload: Record<string, unknown> = {
        name: form.name.trim(),
        hostname: form.hostname.trim(),
        ip_address: form.ip_address.trim(),
        os_family: form.os_family,
        os_version: form.os_version.trim(),
        environment: form.environment,
        owner_area: form.owner_area.trim() || null,
        connection_method: form.connection_method,
        port: Number(form.port),
        username: isSsh ? form.username.trim() : null,
        auth_method: form.auth_method,
        host_key_fingerprint: isSsh ? form.host_key_fingerprint.trim() : null,
        default_profile_id: form.default_profile_id || null,
        authorization_confirmed: form.authorization_confirmed,
        allow_private_target: form.allow_private_target,
        notes: form.notes.trim() || null,
        credential: isSsh ? { secret: form.secret } : undefined,
      };
      return serversApi.create(payload);
    },
    onSuccess: (saved) => {
      notify({
        tone: "success",
        title: editing ? "Servidor actualizado" : "Servidor registrado",
        message:
          editing && saved.authorization_confirmed
            ? "Los cambios de conexión pueden requerir una nueva autorización."
            : "La configuración quedó guardada.",
      });
      onSaved?.(saved);
      onClose();
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setError(err.message);
        if (err.fields?.length) {
          setFieldErrors(
            Object.fromEntries(err.fields.map((field) => [field.field.replace("body.", ""), field.message])),
          );
        }
      } else {
        setError("No fue posible guardar el servidor.");
      }
    },
  });

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="xl"
      title={editing ? "Editar servidor" : "Registrar servidor"}
      description={
        editing
          ? "Los cambios en hostname, IP o puerto revocan la autorización y requieren confirmarla nuevamente."
          : "Registre un objetivo autorizado. Las credenciales se cifran antes de almacenarse."
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            loading={mutation.isPending}
            icon={<ServerIcon className="h-4 w-4" />}
            onClick={() => {
              setError(null);
              if (validate()) mutation.mutate();
            }}
          >
            {editing ? "Guardar cambios" : "Registrar servidor"}
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        {error && <Alert tone="danger">{error}</Alert>}
        {server?.is_simulated && (
          <Alert tone="warning" title="Servidor simulado">
            Este objetivo usa el conector de pruebas y no representa infraestructura real.
          </Alert>
        )}
        <section>
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Identificación</p>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Nombre" required error={fieldErrors.name}>
              <Input value={form.name} onChange={(event) => update("name", event.target.value)} placeholder="Portal web" maxLength={150} />
            </FormField>
            <FormField label="Área responsable" error={fieldErrors.owner_area}>
              <Input value={form.owner_area} onChange={(event) => update("owner_area", event.target.value)} placeholder="Infraestructura" maxLength={150} />
            </FormField>
            <FormField label="Hostname" required error={fieldErrors.hostname}>
              <Input value={form.hostname} onChange={(event) => update("hostname", event.target.value)} placeholder="srv-web-01.empresa.local" />
            </FormField>
            <FormField label="Dirección IP" required error={fieldErrors.ip_address} hint="Se conecta únicamente a esta IP, nunca a un nombre resuelto.">
              <Input value={form.ip_address} onChange={(event) => update("ip_address", event.target.value)} placeholder="10.0.10.15" />
            </FormField>
            <FormField label="Sistema operativo" required>
              <select className="select" value={form.os_family} onChange={(event) => update("os_family", event.target.value)}>
                <option value="ubuntu">Ubuntu</option>
              </select>
            </FormField>
            <FormField label="Versión" required error={fieldErrors.os_version}>
              <select className="select" value={form.os_version} onChange={(event) => update("os_version", event.target.value)}>
                <option value="22.04">22.04 LTS</option>
                <option value="24.04">24.04 LTS</option>
              </select>
            </FormField>
            <FormField label="Entorno" required>
              <select className="select" value={form.environment} onChange={(event) => update("environment", event.target.value)}>
                <option value="production">Producción</option>
                <option value="staging">Pruebas</option>
                <option value="development">Desarrollo</option>
              </select>
            </FormField>
            <FormField label="Perfil CIS" required error={fieldErrors.default_profile_id}>
              <select
                className="select"
                value={form.default_profile_id}
                onChange={(event) => update("default_profile_id", event.target.value)}
              >
                <option value="">Seleccione un perfil</option>
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} · {profile.enabled_control_count} controles
                  </option>
                ))}
              </select>
            </FormField>
          </div>
        </section>

        <section>
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Conexión</p>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Método" required>
              <select
                className="select"
                value={form.connection_method}
                onChange={(event) => update("connection_method", event.target.value as "ssh" | "simulated")}
                disabled={editing}
              >
                <option value="ssh">SSH (solo lectura)</option>
                <option value="simulated">Conector simulado (solo pruebas)</option>
              </select>
            </FormField>
            <FormField label="Puerto" required error={fieldErrors.port}>
              <Input
                type="number"
                min={1}
                max={65535}
                value={form.port}
                onChange={(event) => update("port", event.target.value)}
              />
            </FormField>
            {isSsh && (
              <>
                <FormField label="Usuario técnico" required error={fieldErrors.username}>
                  <Input value={form.username} onChange={(event) => update("username", event.target.value)} placeholder="cis-auditor" autoComplete="off" />
                </FormField>
                <FormField label="Método de autenticación" required>
                  <select className="select" value={form.auth_method} onChange={(event) => update("auth_method", event.target.value as "key" | "password")} disabled={editing}>
                    <option value="key">Clave privada</option>
                    <option value="password">Contraseña</option>
                  </select>
                </FormField>
                <FormField
                  label="Huella de host SSH"
                  required
                  error={fieldErrors.host_key_fingerprint}
                  hint="Obtenga SHA256 con: ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub"
                  className="sm:col-span-2"
                >
                  <Input
                    value={form.host_key_fingerprint}
                    onChange={(event) => update("host_key_fingerprint", event.target.value)}
                    placeholder="SHA256:…"
                    className="font-mono text-xs"
                    disabled={editing}
                  />
                </FormField>
                {!editing && (
                  <FormField
                    label={form.auth_method === "key" ? "Clave privada (se cifra)" : "Contraseña SSH (se cifra)"}
                    required
                    error={fieldErrors.secret}
                    hint="Nunca se muestra después de guardar. No se incluye en logs ni reportes."
                    className="sm:col-span-2"
                  >
                    {form.auth_method === "key" ? (
                      <textarea
                        className="textarea min-h-[120px] font-mono text-xs"
                        value={form.secret}
                        onChange={(event) => update("secret", event.target.value)}
                        placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                        autoComplete="off"
                        spellCheck={false}
                      />
                    ) : (
                      <Input
                        type="password"
                        value={form.secret}
                        onChange={(event) => update("secret", event.target.value)}
                        placeholder="Contraseña del usuario técnico"
                        autoComplete="new-password"
                      />
                    )}
                  </FormField>
                )}
              </>
            )}
          </div>
        </section>

        <section className="rounded-xl border border-line bg-slate-50/60 p-4">
          <p className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
            <Lock className="h-3.5 w-3.5" /> Autorización y alcance
          </p>
          {editing ? (
            <p className="text-[11px] leading-5 text-slate-500">
              La autorización se gestiona desde el detalle del servidor. Cambiar el destino revoca
              automáticamente la autorización vigente.
            </p>
          ) : (
            <>
              <label className="flex items-start gap-2.5 text-xs leading-5 text-slate-600">
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-accent-600 focus:ring-accent-500"
                  checked={form.authorization_confirmed}
                  onChange={(event) => update("authorization_confirmed", event.target.checked)}
                />
                <span>
                  Confirmo que tengo autorización del propietario para auditar este servidor y que la
                  plataforma solo ejecutará comprobaciones de lectura.
                </span>
              </label>
              {fieldErrors.authorization_confirmed && (
                <p className="field-error">{fieldErrors.authorization_confirmed}</p>
              )}
              <label className="mt-3 flex items-start gap-2.5 text-xs leading-5 text-slate-600">
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-accent-600 focus:ring-accent-500"
                  checked={form.allow_private_target}
                  onChange={(event) => update("allow_private_target", event.target.checked)}
                />
                <span>
                  Autorizo explícitamente un objetivo en red privada. Requiere además habilitación
                  global en el backend.
                </span>
              </label>
            </>
          )}
          {editing && (
            <label className="mt-3 flex items-center gap-2.5 text-xs font-medium text-slate-600">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-300 text-accent-600 focus:ring-accent-500"
                checked={form.is_active}
                onChange={(event) => update("is_active", event.target.checked)}
              />
              Servidor activo
            </label>
          )}
        </section>

        <FormField label="Notas" error={fieldErrors.notes}>
          <textarea
            className="textarea"
            value={form.notes}
            onChange={(event) => update("notes", event.target.value)}
            placeholder="Propósito del servidor, ventana de auditoría o contacto responsable."
            maxLength={4000}
          />
        </FormField>

        <div className="flex items-start gap-2 text-[11px] leading-5 text-slate-500">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
          Las conexiones en red privada requieren AUDIT_ALLOW_PRIVATE_TARGETS=true. Loopback, link-local
          y metadatos cloud están bloqueados por política anti-SSRF.
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          <KeyRound className="h-3.5 w-3.5" />
          Cifrado Fernet con clave externa a PostgreSQL.
        </div>
      </div>
    </Modal>
  );
}
