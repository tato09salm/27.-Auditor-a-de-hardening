import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import {
  KeyRound,
  Lock,
  Mail,
  Pencil,
  Plus,
  ShieldCheck,
  UserCheck,
  UserX,
  Users as UsersIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
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
  Pagination,
  SearchField,
  TableSkeleton,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, usersApi } from "../lib/api";
import { dateTime, initials } from "../lib/format";
import { useDebouncedValue } from "../lib/hooks";
import type { UserAdmin } from "../types";

function passwordIsValid(password: string) {
  const classes = [
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^a-zA-Z0-9]/.test(password),
  ].filter(Boolean).length;
  return password.length >= 12 && classes >= 3;
}

function UserCreateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { notify } = useToast();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [roles, setRoles] = useState<string[]>(["analyst"]);
  const [mustChange, setMustChange] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: usersApi.roles, enabled: open });

  const mutation = useMutation({
    mutationFn: () =>
      usersApi.create({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        role_codes: roles,
        must_change_password: mustChange,
      }),
    onSuccess: () => {
      notify({ tone: "success", title: "Usuario creado", message: "Comparta la contraseña temporal por un canal seguro." });
      void queryClient.invalidateQueries({ queryKey: ["users"] });
      setEmail("");
      setFullName("");
      setPassword("");
      setRoles(["analyst"]);
      onClose();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "No fue posible crear el usuario."),
  });

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Crear usuario"
      description="La contraseña temporal debe entregarse por un canal seguro. El usuario deberá cambiarla al ingresar."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button
            loading={mutation.isPending}
            disabled={!email.trim() || fullName.trim().length < 2 || !passwordIsValid(password) || roles.length === 0}
            onClick={() => {
              setError(null);
              mutation.mutate();
            }}
          >
            Crear usuario
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <Alert tone="danger">{error}</Alert>}
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Nombre completo" required>
            <Input value={fullName} onChange={(event) => setFullName(event.target.value)} maxLength={200} />
          </FormField>
          <FormField label="Correo" required>
            <Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="off" />
          </FormField>
        </div>
        <FormField label="Contraseña temporal" required hint="Mínimo 12 caracteres y 3 tipos de caracteres.">
          <Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" />
        </FormField>
        <div>
          <span className="label">Roles</span>
          <div className="grid gap-2 sm:grid-cols-2">
            {(rolesQuery.data ?? []).map((role) => (
              <label key={role.code} className={clsx("flex cursor-pointer items-start gap-2 rounded-xl border p-3 text-xs transition", roles.includes(role.code) ? "border-accent-400 bg-cyan-50/60" : "border-line hover:bg-slate-50")}>
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-accent-600"
                  checked={roles.includes(role.code)}
                  onChange={(event) => {
                    setRoles((current) =>
                      event.target.checked ? [...current, role.code] : current.filter((code) => code !== role.code),
                    );
                  }}
                />
                <span>
                  <span className="block font-semibold text-ink-900">{role.name}</span>
                  <span className="text-[10px] text-slate-400">{role.code}</span>
                </span>
              </label>
            ))}
          </div>
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-600">
          <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-accent-600" checked={mustChange} onChange={(event) => setMustChange(event.target.checked)} />
          Exigir cambio de contraseña en el próximo ingreso
        </label>
      </div>
    </Modal>
  );
}

function UserEditModal({
  user,
  onClose,
}: {
  user: UserAdmin | null;
  onClose: () => void;
}) {
  const { notify } = useToast();
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [roles, setRoles] = useState<string[]>(user?.roles.map((role) => role.code) ?? []);
  const [active, setActive] = useState(user?.is_active ?? true);
  const [error, setError] = useState<string | null>(null);
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: usersApi.roles, enabled: Boolean(user) });

  useEffect(() => {
    if (!user) return;
    setFullName(user.full_name);
    setRoles(user.roles.map((role) => role.code));
    setActive(user.is_active);
    setError(null);
  }, [user]);

  const mutation = useMutation({
    mutationFn: () =>
      usersApi.update(user!.id, {
        full_name: fullName.trim(),
        role_codes: roles,
        is_active: active,
      }),
    onSuccess: () => {
      notify({ tone: "success", title: "Usuario actualizado" });
      void queryClient.invalidateQueries({ queryKey: ["users"] });
      onClose();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "No fue posible actualizar el usuario."),
  });

  return (
    <Modal
      open={Boolean(user)}
      onClose={onClose}
      title="Editar usuario"
      description={user?.email}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button loading={mutation.isPending} disabled={roles.length === 0 || fullName.trim().length < 2} onClick={() => { setError(null); mutation.mutate(); }}>
            Guardar cambios
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <Alert tone="danger">{error}</Alert>}
        <FormField label="Nombre completo" required>
          <Input value={fullName} onChange={(event) => setFullName(event.target.value)} />
        </FormField>
        <div>
          <span className="label">Roles</span>
          <div className="grid gap-2 sm:grid-cols-2">
            {(rolesQuery.data ?? []).map((role) => (
              <label key={role.code} className={clsx("flex cursor-pointer items-center gap-2 rounded-xl border p-3 text-xs transition", roles.includes(role.code) ? "border-accent-400 bg-cyan-50/60" : "border-line hover:bg-slate-50")}>
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-accent-600"
                  checked={roles.includes(role.code)}
                  onChange={(event) =>
                    setRoles((current) => event.target.checked ? [...current, role.code] : current.filter((code) => code !== role.code))
                  }
                />
                <span>
                  <span className="block font-semibold text-ink-900">{role.name}</span>
                  <span className="text-[10px] text-slate-400">{role.code}</span>
                </span>
              </label>
            ))}
          </div>
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-600">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-accent-600"
            checked={active}
            disabled={user?.id === currentUser?.id}
            onChange={(event) => setActive(event.target.checked)}
          />
          Usuario activo
        </label>
        {user?.id === currentUser?.id && <p className="text-[10px] text-slate-400">No puede desactivar su propia cuenta.</p>}
      </div>
    </Modal>
  );
}

function ResetPasswordModal({ user, onClose }: { user: UserAdmin | null; onClose: () => void }) {
  const { notify } = useToast();
  const [password, setPassword] = useState("");
  const [mustChange, setMustChange] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!user) return;
    setPassword("");
    setMustChange(true);
    setError(null);
  }, [user]);
  const mutation = useMutation({
    mutationFn: () => usersApi.resetPassword(user!.id, { new_password: password, must_change_password: mustChange }),
    onSuccess: () => {
      notify({ tone: "success", title: "Contraseña restablecida", message: "Todas las sesiones del usuario fueron revocadas." });
      setPassword("");
      onClose();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "No fue posible restablecer la contraseña."),
  });
  return (
    <Modal
      open={Boolean(user)}
      onClose={onClose}
      title="Restablecer contraseña"
      description={`Se revocarán las sesiones activas de ${user?.full_name ?? "el usuario"}.`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button loading={mutation.isPending} disabled={!passwordIsValid(password)} onClick={() => { setError(null); mutation.mutate(); }}>
            Restablecer
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <Alert tone="danger">{error}</Alert>}
        <FormField label="Nueva contraseña temporal" required hint="Mínimo 12 caracteres y 3 tipos de caracteres.">
          <Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" />
        </FormField>
        <label className="flex items-center gap-2 text-xs text-slate-600">
          <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-accent-600" checked={mustChange} onChange={(event) => setMustChange(event.target.checked)} />
          Exigir cambio en el próximo ingreso
        </label>
      </div>
    </Modal>
  );
}

export function UsersPage() {
  const { hasPermission, user: currentUser } = useAuth();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [role, setRole] = useState("");
  const [active, setActive] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<UserAdmin | null>(null);
  const [resetUser, setResetUser] = useState<UserAdmin | null>(null);

  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: usersApi.roles });
  const query = useQuery({
    queryKey: ["users", debouncedSearch, role, active, page],
    queryFn: () =>
      usersApi.list({
        search: debouncedSearch || undefined,
        role: role || undefined,
        is_active: active === "" ? undefined : active,
        page,
        page_size: 20,
      }),
    placeholderData: keepPreviousData,
  });

  const canManage = hasPermission("users:manage");

  return (
    <>
      <PageHeader
        kicker="Control de acceso"
        title="Usuarios y roles"
        description="El RBAC se verifica en el backend en cada operación. Los accesos, cambios de rol y bloqueos quedan en la bitácora."
        actions={canManage ? <Button icon={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>Crear usuario</Button> : undefined}
      />

      <div className="card mb-5 p-3">
        <div className="grid gap-2.5 sm:grid-cols-3">
          <SearchField value={search} onChange={(value) => { setSearch(value); setPage(1); }} placeholder="Buscar por nombre o correo…" />
          <select className="select py-2 text-xs" value={role} onChange={(event) => { setRole(event.target.value); setPage(1); }}>
            <option value="">Todos los roles</option>
            {(rolesQuery.data ?? []).map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
          </select>
          <select className="select py-2 text-xs" value={active} onChange={(event) => { setActive(event.target.value); setPage(1); }}>
            <option value="">Todos los estados</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>
      </div>

      {query.isLoading ? (
        <TableSkeleton rows={6} cols={6} />
      ) : query.isError ? (
        <ErrorState message="No se pudieron consultar los usuarios." onRetry={() => void query.refetch()} />
      ) : query.data?.items.length ? (
        <div className="table-shell">
          <div className="overflow-x-auto">
            <table className="data-table min-w-[860px]">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Roles</th>
                  <th>Estado</th>
                  <th>Último acceso</th>
                  <th>Creado</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink-900 text-[10px] font-bold text-accent-400">
                          {initials(item.full_name)}
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-ink-900">
                            {item.full_name}
                            {item.id === currentUser?.id && <span className="ml-1.5 text-[9px] font-normal text-slate-400">(usted)</span>}
                          </p>
                          <p className="text-[10px] text-slate-400">{item.email}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        {item.roles.map((itemRole) => <Badge key={itemRole.code} tone="neutral">{itemRole.name}</Badge>)}
                      </div>
                    </td>
                    <td>
                      <Badge tone={item.is_active ? "success" : "neutral"} dot>{item.is_active ? "Activo" : "Inactivo"}</Badge>
                      {item.locked_until && <p className="mt-1 text-[9px] text-red-500">Bloqueado hasta {dateTime(item.locked_until)}</p>}
                    </td>
                    <td className="whitespace-nowrap text-xs text-slate-500">{item.last_login_at ? dateTime(item.last_login_at) : "Nunca"}</td>
                    <td className="whitespace-nowrap text-xs text-slate-500">{dateTime(item.created_at)}</td>
                    <td>
                      {canManage && (
                        <div className="flex items-center gap-1">
                          <button className="icon-btn" onClick={() => setEditUser(item)} aria-label="Editar usuario"><Pencil className="h-4 w-4" /></button>
                          <button className="icon-btn" onClick={() => setResetUser(item)} aria-label="Restablecer contraseña"><KeyRound className="h-4 w-4" /></button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={query.data.page} pageSize={query.data.page_size} total={query.data.total} onPageChange={setPage} />
        </div>
      ) : (
        <div className="card">
          <EmptyState icon={<UsersIcon className="h-5 w-5" />} title="Sin usuarios" description="No hay usuarios que coincidan con los filtros." />
        </div>
      )}

      <Card className="mt-5 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
        {(rolesQuery.data ?? []).map((item) => (
          <div key={item.code} className="rounded-xl border border-line bg-slate-50/50 p-3">
            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <ShieldCheck className="h-3.5 w-3.5 text-accent-600" /> {item.name}
            </div>
            <p className="mt-1 text-[10px] leading-5 text-slate-400">
              {item.code === "admin" ? "Control total de la organización." : item.code === "auditor" ? "Ejecuta auditorías y revisa propuestas." : item.code === "analyst" ? "Gestiona hallazgos y solicita IA." : "Solo consulta dashboards e informes."}
            </p>
          </div>
        ))}
      </Card>

      <UserCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <UserEditModal user={editUser} onClose={() => setEditUser(null)} />
      <ResetPasswordModal user={resetUser} onClose={() => setResetUser(null)} />
    </>
  );
}
