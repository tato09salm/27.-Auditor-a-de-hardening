import { useMutation, useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import {
  BookOpenCheck,
  CheckCircle2,
  ChevronRight,
  Layers3,
  Plus,
  Settings2,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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
  PageLoader,
  PageHeader,
  SectionHeader,
  SeverityBadge,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, profilesApi } from "../lib/api";
import { dateTime } from "../lib/format";
import type { Control, Profile, ProfileDetail } from "../types";

function ProfileEditorModal({
  open,
  onClose,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { notify } = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [benchmarkId, setBenchmarkId] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isDefault, setIsDefault] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const benchmarksQuery = useQuery({
    queryKey: ["benchmarks"],
    queryFn: profilesApi.benchmarks,
    enabled: open,
  });
  const controlsQuery = useQuery({
    queryKey: ["benchmark-controls", benchmarkId],
    queryFn: () => profilesApi.controls(benchmarkId),
    enabled: open && Boolean(benchmarkId),
  });

  useEffect(() => {
    if (!open) return;
    setName("");
    setDescription("");
    setSelected(new Set());
    setIsDefault(false);
    setError(null);
  }, [open]);

  useEffect(() => {
    if (!benchmarkId && benchmarksQuery.data?.length) {
      setBenchmarkId(benchmarksQuery.data[0].id);
    }
  }, [benchmarkId, benchmarksQuery.data]);

  useEffect(() => {
    if (controlsQuery.data) {
      setSelected(new Set(controlsQuery.data.map((control) => control.id)));
    }
  }, [controlsQuery.data]);

  const mutation = useMutation({
    mutationFn: () =>
      profilesApi.create({
        name: name.trim(),
        description: description.trim() || null,
        benchmark_id: benchmarkId,
        control_ids: Array.from(selected),
        is_default: isDefault,
      }),
    onSuccess: () => {
      notify({ tone: "success", title: "Perfil creado", message: "El perfil está disponible para auditorías." });
      onSaved();
      onClose();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "No fue posible crear el perfil."),
  });

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="xl"
      title="Nuevo perfil de auditoría"
      description="Seleccione el benchmark y los controles que se evaluarán. El perfil queda versionado por referencia al benchmark."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button
            loading={mutation.isPending}
            disabled={!name.trim() || !benchmarkId || selected.size === 0}
            onClick={() => mutation.mutate()}
          >
            Crear perfil
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        {error && <Alert tone="danger">{error}</Alert>}
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Nombre" required>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Línea base servidores web" maxLength={150} />
          </FormField>
          <FormField label="Benchmark" required>
            <select className="select" value={benchmarkId} onChange={(event) => { setBenchmarkId(event.target.value); setSelected(new Set()); }}>
              {(benchmarksQuery.data ?? []).map((benchmark) => (
                <option key={benchmark.id} value={benchmark.id}>
                  {benchmark.name} v{benchmark.version}
                </option>
              ))}
            </select>
          </FormField>
        </div>
        <FormField label="Descripción">
          <textarea className="textarea" value={description} onChange={(event) => setDescription(event.target.value)} maxLength={2000} placeholder="Alcance del perfil y criterios de aplicación." />
        </FormField>
        <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
          <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-accent-600" checked={isDefault} onChange={(event) => setIsDefault(event.target.checked)} />
          Usar como perfil por defecto de la organización
        </label>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
              Controles ({selected.size}/{controlsQuery.data?.length ?? 0})
            </p>
            <button
              className="text-[10px] font-semibold text-accent-700 hover:underline"
              onClick={() => {
                const all = controlsQuery.data ?? [];
                setSelected(selected.size === all.length ? new Set() : new Set(all.map((item) => item.id)));
              }}
            >
              {selected.size === (controlsQuery.data?.length ?? 0) ? "Quitar todos" : "Seleccionar todos"}
            </button>
          </div>
          <div className="max-h-[330px] space-y-1.5 overflow-y-auto rounded-xl border border-line p-2">
            {(controlsQuery.data ?? []).map((control) => (
              <label key={control.id} className="flex cursor-pointer items-start gap-3 rounded-lg p-2.5 transition hover:bg-slate-50">
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-accent-600"
                  checked={selected.has(control.id)}
                  onChange={() => toggle(control.id)}
                />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-ink-900">{control.title}</span>
                    <SeverityBadge severity={control.severity} />
                    {!control.is_official_mapping && <Badge tone="neutral">Interno</Badge>}
                  </span>
                  <span className="mt-0.5 block font-mono text-[10px] text-slate-400">
                    {control.cis_reference ?? control.code} · {control.category}
                  </span>
                </span>
              </label>
            ))}
          </div>
        </div>
        <Alert tone="info">
          Los controles internos están identificados como tales y no representan un mapeo oficial de CIS.
        </Alert>
      </div>
    </Modal>
  );
}

function ProfileDetailModal({
  profile,
  onClose,
}: {
  profile: Profile | null;
  onClose: () => void;
}) {
  const query = useQuery({
    queryKey: ["profile", profile?.id],
    queryFn: () => profilesApi.get(profile!.id),
    enabled: Boolean(profile),
  });
  const detail = query.data;

  return (
    <Modal
      open={Boolean(profile)}
      onClose={onClose}
      size="xl"
      title={profile?.name ?? "Perfil"}
      description={profile?.benchmark_name ? `${profile.benchmark_name} v${profile.benchmark_version}` : undefined}
      footer={<Button variant="secondary" onClick={onClose}>Cerrar</Button>}
    >
      {query.isLoading ? (
        <PageLoader label="Cargando perfil…" />
      ) : detail ? (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-line bg-slate-50/60 p-3">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Controles</p>
              <p className="mt-1 text-lg font-bold text-ink-900">{detail.control_count}</p>
            </div>
            <div className="rounded-xl border border-line bg-slate-50/60 p-3">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Benchmark</p>
              <p className="mt-1 text-xs font-semibold text-ink-900">{detail.benchmark_name} v{detail.benchmark_version}</p>
            </div>
            <div className="rounded-xl border border-line bg-slate-50/60 p-3">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Actualizado</p>
              <p className="mt-1 text-xs font-semibold text-ink-900">{dateTime(detail.updated_at)}</p>
            </div>
          </div>
          {detail.description && <p className="text-xs leading-6 text-slate-600">{detail.description}</p>}
          <div>
            <SectionHeader title="Controles incluidos" description="Cada control conserva su criterio, severidad y mapeo." />
            <div className="mt-3 divide-y divide-line rounded-xl border border-line">
              {detail.controls.map((control) => (
                <details key={control.id} className="group">
                  <summary className="flex cursor-pointer list-none items-center gap-3 px-3.5 py-3 transition hover:bg-slate-50">
                    <span className="font-mono text-[10px] font-bold text-slate-400">{control.code}</span>
                    <span className="flex-1 text-xs font-semibold text-ink-900">{control.title}</span>
                    <SeverityBadge severity={control.severity} />
                    {control.is_official_mapping ? (
                      <Badge tone="accent">CIS {control.cis_reference}</Badge>
                    ) : (
                      <Badge tone="neutral">Interno</Badge>
                    )}
                    <ChevronRight className="h-4 w-4 text-slate-300 transition group-open:rotate-90" />
                  </summary>
                  <div className="space-y-3 bg-slate-50/60 px-4 py-4">
                    <p className="text-[11px] leading-6 text-slate-600">{control.description}</p>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Guía de corrección</p>
                      <p className="mt-1 text-[11px] leading-6 text-slate-600">{control.remediation_guidance}</p>
                    </div>
                    {control.mapping_notes && (
                      <p className="rounded-lg bg-white p-2.5 text-[10px] leading-5 text-slate-500">
                        <b>Mapeo:</b> {control.mapping_notes}
                      </p>
                    )}
                  </div>
                </details>
              ))}
            </div>
          </div>
          <Alert tone="info">
            La ejecución usa esta definición como referencia. Cambios futuros al benchmark requieren un
            nuevo perfil o una migración controlada.
          </Alert>
        </div>
      ) : (
        <ErrorState />
      )}
    </Modal>
  );
}

export function ProfilesPage() {
  const { hasPermission } = useAuth();
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<Profile | null>(null);
  const query = useQuery({ queryKey: ["profiles"], queryFn: profilesApi.list });

  return (
    <>
      <PageHeader
        kicker="Catálogo versionado"
        title="Perfiles CIS"
        description="Agrupaciones de controles que definen el alcance de cada auditoría. Los identificadores CIS y los controles internos están diferenciados."
        actions={
          hasPermission("profiles:manage") ? (
            <Button icon={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>
              Nuevo perfil
            </Button>
          ) : undefined
        }
      />

      {query.isLoading ? (
        <PageLoader />
      ) : query.isError ? (
        <ErrorState message="No se pudieron consultar los perfiles." onRetry={() => void query.refetch()} />
      ) : query.data?.length ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {query.data.map((profile) => (
            <button
              key={profile.id}
              className="card group p-5 text-left transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lift"
              onClick={() => setSelected(profile)}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50 text-accent-700">
                  <Layers3 className="h-5 w-5" />
                </div>
                <div className="flex flex-wrap justify-end gap-1.5">
                  {profile.is_default && <Badge tone="accent">Por defecto</Badge>}
                  {!profile.is_active && <Badge tone="neutral">Inactivo</Badge>}
                </div>
              </div>
              <h2 className="mt-4 text-sm font-bold text-ink-900 group-hover:text-accent-800">{profile.name}</h2>
              <p className="mt-1 line-clamp-2 min-h-[40px] text-[11px] leading-5 text-slate-500">
                {profile.description ?? "Sin descripción."}
              </p>
              <div className="mt-4 flex items-center justify-between border-t border-line pt-3.5">
                <div className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-500">
                  <BookOpenCheck className="h-3.5 w-3.5" />
                  {profile.enabled_control_count} controles
                </div>
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-accent-700">
                  Ver detalle <ChevronRight className="h-3.5 w-3.5" />
                </span>
              </div>
              <div className="mt-3 truncate text-[10px] text-slate-400">{profile.benchmark_name} v{profile.benchmark_version}</div>
            </button>
          ))}
        </div>
      ) : (
        <Card>
          <EmptyState
            icon={<Layers3 className="h-5 w-5" />}
            title="Sin perfiles configurados"
            description="Cree un perfil con los controles que desea evaluar."
            action={hasPermission("profiles:manage") ? <Button onClick={() => setCreateOpen(true)}>Nuevo perfil</Button> : undefined}
          />
        </Card>
      )}

      <Card className="mt-5 flex flex-col gap-3 border-dashed p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
            <ShieldCheck className="h-4 w-4" />
          </span>
          <div>
            <p className="text-xs font-semibold text-ink-900">Trazabilidad del benchmark</p>
            <p className="mt-0.5 text-[11px] leading-5 text-slate-500">
              Los resultados guardan la versión del benchmark usada. Las actualizaciones de CIS no alteran
              auditorías históricas.
            </p>
          </div>
        </div>
        <Settings2 className="hidden h-5 w-5 text-slate-300 sm:block" />
      </Card>

      <ProfileEditorModal open={createOpen} onClose={() => setCreateOpen(false)} onSaved={() => void query.refetch()} />
      <ProfileDetailModal profile={selected} onClose={() => setSelected(null)} />
    </>
  );
}
