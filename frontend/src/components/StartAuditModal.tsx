import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Play, Radar, Server as ServerIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, auditsApi, profilesApi, serversApi } from "../lib/api";
import { Alert, Button, FormField, Modal } from "./ui";

export function StartAuditModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { hasPermission } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();
  const [serverId, setServerId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const serversQuery = useQuery({
    queryKey: ["servers", "audit-picker"],
    queryFn: () => serversApi.list({ page_size: 200, is_active: true }),
    enabled: open && hasPermission("servers:read"),
  });
  const profilesQuery = useQuery({
    queryKey: ["profiles"],
    queryFn: profilesApi.list,
    enabled: open && hasPermission("profiles:read"),
  });

  const servers = useMemo(
    () => (serversQuery.data?.items ?? []).filter((server) => server.is_active),
    [serversQuery.data],
  );
  const selected = servers.find((server) => server.id === serverId);
  const profiles = profilesQuery.data ?? [];

  useEffect(() => {
    if (!open) {
      setServerId("");
      setProfileId("");
      setError(null);
    }
  }, [open]);

  useEffect(() => {
    if (selected?.default_profile_id) setProfileId(selected.default_profile_id);
  }, [selected?.id, selected?.default_profile_id]);

  const mutation = useMutation({
    mutationFn: () =>
      auditsApi.create({
        server_id: serverId,
        profile_id: profileId || undefined,
      }),
    onSuccess: (run) => {
      notify({
        tone: "success",
        title: "Auditoría en cola",
        message: "La ejecución comenzó. Los resultados aparecerán al finalizar.",
      });
      onClose();
      navigate(`/audits/${run.id}`);
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "No fue posible iniciar la auditoría.");
    },
  });

  const canSubmit = Boolean(serverId && profileId && selected?.authorization_confirmed);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Ejecutar auditoría"
      description="Seleccione un servidor autorizado y un perfil. La ejecución es de solo lectura."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            icon={<Play className="h-4 w-4" />}
            loading={mutation.isPending}
            disabled={!canSubmit}
            onClick={() => {
              setError(null);
              mutation.mutate();
            }}
          >
            Iniciar auditoría
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <Alert tone="danger">{error}</Alert>}
        <FormField label="Servidor" required>
          <select
            className="select"
            value={serverId}
            onChange={(event) => setServerId(event.target.value)}
          >
            <option value="">Seleccione un servidor</option>
            {servers.map((server) => (
              <option key={server.id} value={server.id} disabled={!server.authorization_confirmed}>
                {server.name} · {server.hostname}
                {server.is_simulated ? " (simulado)" : ""}
                {!server.authorization_confirmed ? " — no autorizado" : ""}
              </option>
            ))}
          </select>
        </FormField>
        {serversQuery.isLoading && <p className="text-xs text-slate-400">Cargando servidores…</p>}
        {servers.length === 0 && !serversQuery.isLoading && (
          <Alert tone="info" title="No hay servidores disponibles">
            Registre y autorice un servidor antes de ejecutar una auditoría.
          </Alert>
        )}
        {selected && !selected.authorization_confirmed && (
          <Alert tone="warning" title="Servidor sin autorización">
            La auditoría no puede ejecutarse hasta que un administrador confirme la autorización.
          </Alert>
        )}
        <FormField label="Perfil de auditoría" required>
          <select
            className="select"
            value={profileId}
            onChange={(event) => setProfileId(event.target.value)}
          >
            <option value="">Seleccione un perfil</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.name} · {profile.enabled_control_count} controles
              </option>
            ))}
          </select>
        </FormField>
        {selected && (
          <div className="grid gap-3 rounded-xl border border-line bg-slate-50/70 p-3.5 sm:grid-cols-2">
            <div className="flex items-start gap-2">
              <ServerIcon className="mt-0.5 h-4 w-4 text-slate-400" />
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Objetivo</p>
                <p className="mt-0.5 text-xs font-semibold text-slate-700">
                  {selected.ip_address}:{selected.port}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Radar className="mt-0.5 h-4 w-4 text-slate-400" />
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Método</p>
                <p className="mt-0.5 text-xs font-semibold text-slate-700">
                  {selected.connection_method === "ssh" ? "SSH de solo lectura" : "Conector simulado"}
                </p>
              </div>
            </div>
          </div>
        )}
        <div className="flex items-start gap-2 text-[11px] leading-5 text-slate-500">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
          No se ejecutarán comandos de corrección. El porcentaje no constituye una certificación CIS.
        </div>
      </div>
    </Modal>
  );
}
