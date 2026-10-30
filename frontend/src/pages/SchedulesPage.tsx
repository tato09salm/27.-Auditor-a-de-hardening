import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { CalendarClock, Clock3, Plus, Power, Workflow } from "lucide-react";
import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  FormField,
  Input,
  Modal,
  PageHeader,
  SectionHeader,
  TableSkeleton,
} from "../components/ui";
import { useToast } from "../context/Toast";
import { ApiError, profilesApi, schedulesApi, serversApi } from "../lib/api";
import { dateTime } from "../lib/format";
import type { Schedule } from "../types";

const cronPresets = [
  { label: "Diariamente a las 03:00", value: "0 3 * * *" },
  { label: "Cada 6 horas", value: "0 */6 * * *" },
  { label: "Lunes a las 02:00", value: "0 2 * * 1" },
  { label: "Primer día del mes, 04:00", value: "0 4 1 * *" },
  { label: "Personalizado", value: "custom" },
];

export function SchedulesPage() {
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [serverId, setServerId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [preset, setPreset] = useState("0 3 * * *");
  const [customCron, setCustomCron] = useState("");
  const [timezone, setTimezone] = useState("America/Lima");
  const [enabled, setEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const schedulesQuery = useQuery({ queryKey: ["schedules"], queryFn: schedulesApi.list });
  const serversQuery = useQuery({
    queryKey: ["servers", "schedules"],
    queryFn: () => serversApi.list({ page_size: 200, is_active: true }),
  });
  const profilesQuery = useQuery({ queryKey: ["profiles"], queryFn: profilesApi.list });

  const createMutation = useMutation({
    mutationFn: () =>
      schedulesApi.create({
        name: name.trim(),
        server_id: serverId,
        profile_id: profileId,
        cron_expression: preset === "custom" ? customCron.trim() : preset,
        timezone,
        is_enabled: enabled,
      }),
    onSuccess: () => {
      notify({ tone: "success", title: "Programación creada", message: "n8n podrá ejecutar las auditorías vencidas." });
      setCreateOpen(false);
      setName("");
      setServerId("");
      setProfileId("");
      setCustomCron("");
      void queryClient.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "No fue posible crear la programación."),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, next }: { id: string; next: boolean }) =>
      schedulesApi.update(id, { is_enabled: next }),
    onSuccess: (_, variables) => {
      notify({
        tone: "success",
        title: variables.next ? "Programación habilitada" : "Programación pausada",
      });
      void queryClient.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: (err) =>
      notify({ tone: "error", title: "No se pudo cambiar", message: err instanceof ApiError ? err.message : undefined }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => schedulesApi.disable(id),
    onSuccess: () => {
      notify({ tone: "success", title: "Programación deshabilitada" });
      void queryClient.invalidateQueries({ queryKey: ["schedules"] });
    },
  });

  const canSubmit =
    name.trim().length >= 2 &&
    serverId &&
    profileId &&
    (preset !== "custom" || customCron.trim().split(/\s+/).length === 5);

  function openCreate() {
    setError(null);
    setCreateOpen(true);
    if (!profileId && profilesQuery.data?.length) setProfileId(profilesQuery.data[0].id);
  }

  return (
    <>
      <PageHeader
        kicker="Automatización"
        title="Programación"
        description="Defina auditorías periódicas. n8n consulta las programaciones vencidas mediante una API key con alcance limitado y el backend evita ejecuciones duplicadas."
        actions={<Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>Nueva programación</Button>}
      />

      <Card className="mb-5 flex flex-col gap-3 border-dashed p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
            <Workflow className="h-4 w-4" />
          </span>
          <div>
            <p className="text-xs font-semibold text-ink-900">Flujo n8n: auditoría programada</p>
            <p className="mt-0.5 text-[11px] leading-5 text-slate-500">
              Cron de n8n → <span className="font-mono text-[10px]">POST /automation/audits/run-due</span> → ejecución y bitácora.
              Las programaciones pausadas no se ejecutan.
            </p>
          </div>
        </div>
        <Badge tone="neutral">La programación no envía correos</Badge>
      </Card>

      {schedulesQuery.isLoading ? (
        <TableSkeleton rows={5} cols={6} />
      ) : schedulesQuery.isError ? (
        <ErrorState message="No se pudieron consultar las programaciones." onRetry={() => void schedulesQuery.refetch()} />
      ) : schedulesQuery.data?.length ? (
        <div className="table-shell">
          <div className="overflow-x-auto">
            <table className="data-table min-w-[980px]">
              <thead>
                <tr>
                  <th>Programación</th>
                  <th>Servidor</th>
                  <th>Perfil</th>
                  <th>Cron</th>
                  <th>Próxima ejecución</th>
                  <th>Última ejecución</th>
                  <th>Estado</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {schedulesQuery.data.map((schedule: Schedule) => (
                  <tr key={schedule.id}>
                    <td>
                      <p className="text-xs font-semibold text-ink-900">{schedule.name}</p>
                      <p className="mt-0.5 text-[10px] text-slate-400">{schedule.timezone}</p>
                    </td>
                    <td className="text-xs">{schedule.server_name}</td>
                    <td className="max-w-[200px] truncate text-xs">{schedule.profile_name}</td>
                    <td>
                      <code className="rounded-md border border-line bg-slate-50 px-2 py-1 font-mono text-[10px] text-slate-600">
                        {schedule.cron_expression}
                      </code>
                    </td>
                    <td className="whitespace-nowrap text-xs text-slate-500">
                      {schedule.next_run_at ? dateTime(schedule.next_run_at) : "—"}
                    </td>
                    <td className="whitespace-nowrap text-xs text-slate-500">
                      {schedule.last_run_at ? dateTime(schedule.last_run_at) : "Nunca"}
                    </td>
                    <td>
                      <Badge tone={schedule.is_enabled ? "success" : "neutral"} dot>
                        {schedule.is_enabled ? "Activa" : "Pausada"}
                      </Badge>
                    </td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button
                          className="icon-btn"
                          onClick={() => toggleMutation.mutate({ id: schedule.id, next: !schedule.is_enabled })}
                          title={schedule.is_enabled ? "Pausar" : "Habilitar"}
                          aria-label={schedule.is_enabled ? "Pausar programación" : "Habilitar programación"}
                        >
                          <Power className={clsx("h-4 w-4", schedule.is_enabled ? "text-emerald-600" : "text-slate-400")} />
                        </button>
                        <button
                          className="text-[10px] font-semibold text-red-500 hover:underline"
                          onClick={() => {
                            if (window.confirm("¿Deshabilitar esta programación? No se borrará el historial.")) {
                              deleteMutation.mutate(schedule.id);
                            }
                          }}
                        >
                          Deshabilitar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <Card>
          <EmptyState
            icon={<CalendarClock className="h-5 w-5" />}
            title="Sin programaciones"
            description="Cree una programación para que n8n dispare auditorías periódicas."
            action={<Button onClick={openCreate}>Nueva programación</Button>}
          />
        </Card>
      )}

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Nueva programación"
        description="El cron se interpreta en la zona horaria indicada. La próxima ejecución se calcula en el backend."
        footer={
          <>
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>Cancelar</Button>
            <Button
              loading={createMutation.isPending}
              disabled={!canSubmit}
              onClick={() => {
                setError(null);
                createMutation.mutate();
              }}
            >
              Crear programación
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {error && <Alert tone="danger">{error}</Alert>}
          <FormField label="Nombre" required>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Auditoría nocturna producción" maxLength={150} />
          </FormField>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Servidor" required>
              <select className="select" value={serverId} onChange={(event) => setServerId(event.target.value)}>
                <option value="">Seleccione un servidor</option>
                {(serversQuery.data?.items ?? []).map((server) => (
                  <option key={server.id} value={server.id} disabled={!server.authorization_confirmed}>
                    {server.name}{!server.authorization_confirmed ? " — no autorizado" : ""}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Perfil" required>
              <select className="select" value={profileId} onChange={(event) => setProfileId(event.target.value)}>
                <option value="">Seleccione un perfil</option>
                {(profilesQuery.data ?? []).map((profile) => (
                  <option key={profile.id} value={profile.id}>{profile.name}</option>
                ))}
              </select>
            </FormField>
            <FormField label="Frecuencia" required>
              <select className="select" value={preset} onChange={(event) => setPreset(event.target.value)}>
                {cronPresets.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </FormField>
            <FormField label="Zona horaria" required>
              <select className="select" value={timezone} onChange={(event) => setTimezone(event.target.value)}>
                <option value="America/Lima">America/Lima (UTC-5)</option>
                <option value="America/Bogota">America/Bogota (UTC-5)</option>
                <option value="America/Mexico_City">America/Mexico_City (UTC-6)</option>
                <option value="America/Santiago">America/Santiago</option>
                <option value="America/Argentina/Buenos_Aires">America/Argentina/Buenos_Aires</option>
                <option value="UTC">UTC</option>
              </select>
            </FormField>
          </div>
          {preset === "custom" && (
            <FormField label="Expresión cron" required hint="Cinco campos: minuto hora día mes día-semana. Ejemplo: 0 3 * * *">
              <Input className="font-mono" value={customCron} onChange={(event) => setCustomCron(event.target.value)} placeholder="0 3 * * *" />
            </FormField>
          )}
          <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
            <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-accent-600" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} />
            Programación habilitada
          </label>
          <div className="flex items-start gap-2 rounded-xl border border-line bg-slate-50 p-3 text-[10px] leading-5 text-slate-500">
            <Clock3 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            n8n debe ejecutar el flujo con una API key de alcance <code className="font-mono">automation:execute</code>.
            Si no se ejecuta, la programación permanece pendiente sin generar duplicados.
          </div>
        </div>
      </Modal>
    </>
  );
}
