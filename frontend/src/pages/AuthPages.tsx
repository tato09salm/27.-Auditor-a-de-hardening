import clsx from "clsx";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Eye,
  EyeOff,
  Fingerprint,
  KeyRound,
  LockKeyhole,
  RefreshCcw,
  ServerCog,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useMemo, useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Logo } from "../components/Logo";
import { Alert, Button, FormField, Input } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/Toast";
import { ApiError, authApi } from "../lib/api";

function PasswordInput({
  value,
  onChange,
  placeholder,
  autoComplete,
  id,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoComplete?: string;
  id?: string;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <Input
        id={id}
        type={visible ? "text" : "password"}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        className="pr-11"
      />
      <button
        type="button"
        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-700"
        onClick={() => setVisible((current) => !current)}
        aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}

function AuthArtwork() {
  const points = [
    { icon: <ShieldCheck className="h-4 w-4" />, title: "Controles verificables", text: "Evidencia técnica de cada resultado" },
    { icon: <Fingerprint className="h-4 w-4" />, title: "Acceso con mínimo privilegio", text: "RBAC y bitácora append-only" },
    { icon: <Sparkles className="h-4 w-4" />, title: "IA con revisión humana", text: "Nunca ejecuta comandos" },
    { icon: <ServerCog className="h-4 w-4" />, title: "Auditoría de solo lectura", text: "Sin cambios automáticos" },
  ];
  return (
    <div className="relative hidden overflow-hidden rounded-[28px] bg-ink-950 p-9 text-white lg:flex lg:flex-col lg:justify-between xl:p-12">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(6,182,212,0.22),transparent_38%),radial-gradient(circle_at_90%_90%,rgba(37,99,235,0.18),transparent_45%)]" />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px)",
          backgroundSize: "42px 42px",
        }}
      />
      <div className="relative">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-cyan-300">
          <span className="h-1.5 w-1.5 rounded-full bg-accent-400" />
          Plataforma de hardening continuo
        </div>
        <h1 className="mt-8 max-w-lg text-balance text-4xl font-bold leading-[1.12] tracking-tight">
          Convierte configuraciones inseguras en evidencia accionable.
        </h1>
        <p className="mt-5 max-w-md text-sm leading-7 text-slate-400">
          Evalúa servidores Linux frente a controles CIS, prioriza hallazgos y genera planes de
          corrección revisables, sin tocar la infraestructura.
        </p>
        <div className="mt-10 grid max-w-lg gap-3 sm:grid-cols-2">
          {points.map((item) => (
            <div
              key={item.title}
              className="rounded-xl border border-white/[0.08] bg-white/[0.035] p-3.5 backdrop-blur-sm"
            >
              <div className="flex items-center gap-2 text-accent-400">{item.icon}</div>
              <p className="mt-2.5 text-xs font-semibold text-white">{item.title}</p>
              <p className="mt-0.5 text-[11px] leading-5 text-slate-500">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="relative mt-10">
        <div className="flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-ink-900/60 p-4 backdrop-blur">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-500/15 text-accent-400">
            <LockKeyhole className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-white">Secretos protegidos</p>
            <p className="mt-0.5 text-[11px] leading-5 text-slate-500">
              Credenciales cifradas, claves privadas fuera de logs y reportes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-surface p-3 sm:p-5 lg:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-1.5rem)] max-w-[1240px] gap-5 lg:min-h-[calc(100vh-3rem)] lg:grid-cols-[1.08fr_0.92fr]">
        <AuthArtwork />
        <div className="flex items-center justify-center rounded-[28px] border border-line bg-white px-5 py-10 shadow-card sm:px-10 lg:px-12">
          <div className="w-full max-w-[380px]">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function LoadingScreen() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-ink-950">
      <div className="relative">
        <div className="absolute inset-0 animate-ping rounded-3xl bg-accent-500/10" />
        <Logo size={64} />
      </div>
      <p className="mt-6 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Preparando consola
      </p>
      <div className="mt-4 h-1 w-32 overflow-hidden rounded-full bg-white/10">
        <div className="h-full w-1/2 animate-shimmer rounded-full bg-accent-500" />
      </div>
    </div>
  );
}

export function OfflinePage() {
  const { bootError, retryBoot } = useAuth();
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface p-6">
      <div className="w-full max-w-md rounded-2xl border border-line bg-white p-8 text-center shadow-card">
        <Logo size={48} className="justify-center" />
        <h1 className="mt-6 text-xl font-bold text-ink-950">Servicio no disponible</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          {bootError ?? "No fue posible contactar la API."}
        </p>
        <Alert tone="info" className="mt-5 text-left">
          Verifique que el backend esté iniciado y que las migraciones se hayan aplicado.
        </Alert>
        <Button variant="primary" className="mt-6 w-full" icon={<RefreshCcw className="h-4 w-4" />} onClick={retryBoot}>
          Reintentar conexión
        </Button>
      </div>
    </div>
  );
}

export function LoginPage() {
  const { login, setupStatus } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email.trim(), password);
      notify({ tone: "success", title: "Sesión iniciada", message: "Bienvenido a la consola de hardening." });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No fue posible iniciar sesión.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <div className="flex items-center justify-between">
        <Logo size={40} showWordmark />
        <span className="rounded-full border border-line bg-slate-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
          v{setupStatus?.version ?? "1.0"}
        </span>
      </div>
      <div className="mt-9">
        <p className="section-kicker">Acceso seguro</p>
        <h2 className="mt-1.5 text-2xl font-bold tracking-tight text-ink-950">Iniciar sesión</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          Ingrese con su cuenta corporativa. Los accesos quedan registrados en la bitácora.
        </p>
      </div>
      {error && (
        <Alert tone="danger" className="mt-5" title="No se pudo autenticar">
          {error}
        </Alert>
      )}
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <FormField label="Correo electrónico" required>
          <Input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="nombre@organizacion.com"
            autoComplete="username"
            required
            autoFocus
          />
        </FormField>
        <FormField label="Contraseña" required>
          <PasswordInput
            value={password}
            onChange={setPassword}
            placeholder="Ingrese su contraseña"
            autoComplete="current-password"
          />
        </FormField>
        <Button type="submit" variant="primary" className="w-full" loading={loading} icon={<ArrowRight className="h-4 w-4" />}>
          Acceder a la consola
        </Button>
      </form>
      <div className="mt-7 rounded-xl border border-line bg-slate-50/60 p-3.5">
        <p className="flex items-start gap-2 text-[11px] leading-5 text-slate-500">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-accent-600" />
          No hay credenciales predeterminadas. Si perdió el acceso, contacte al administrador de su
          organización.
        </p>
      </div>
    </AuthLayout>
  );
}

function slugify(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100);
}

function passwordChecks(password: string, email: string) {
  const classes = [
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^a-zA-Z0-9]/.test(password),
  ].filter(Boolean).length;
  const local = email.split("@")[0]?.toLowerCase() ?? "";
  return [
    { label: "12 caracteres o más", ok: password.length >= 12 },
    { label: "Al menos 3 tipos de caracteres", ok: classes >= 3 },
    { label: "No contiene el correo", ok: !local || local.length < 4 || !password.toLowerCase().includes(local) },
  ];
}

export function SetupPage() {
  const { initialize } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();
  const [organization, setOrganization] = useState("");
  const [slug, setSlug] = useState("");
  const [slugTouched, setSlugTouched] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const checks = useMemo(() => passwordChecks(password, email), [password, email]);
  const valid =
    checks.every((check) => check.ok) &&
    password === confirm &&
    organization.trim().length >= 2 &&
    (slug || slugify(organization)).length >= 2;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!valid) {
      setError("Revise la organización y los requisitos de contraseña.");
      return;
    }
    setLoading(true);
    try {
      await initialize({
        organization_name: organization.trim(),
        organization_slug: slug || slugify(organization),
        admin_full_name: fullName.trim(),
        admin_email: email.trim(),
        admin_password: password,
      });
      notify({ tone: "success", title: "Plataforma inicializada", message: "Ya puede comenzar a registrar servidores." });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No fue posible inicializar la plataforma.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <Logo size={40} showWordmark />
      <div className="mt-9">
        <p className="section-kicker">Primera configuración</p>
        <h2 className="mt-1.5 text-2xl font-bold tracking-tight text-ink-950">Cree la cuenta administradora</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          No existen usuarios todavía. Este paso se ejecuta una sola vez y crea la organización inicial.
        </p>
      </div>
      {error && (
        <Alert tone="danger" className="mt-5" title="No se pudo completar la instalación">
          {error}
        </Alert>
      )}
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Organización" required>
            <Input
              value={organization}
              onChange={(event) => {
                setOrganization(event.target.value);
                if (!slugTouched) setSlug(slugify(event.target.value));
              }}
              placeholder="Mi empresa"
              maxLength={200}
              required
            />
          </FormField>
          <FormField label="Identificador" required hint="Solo minúsculas, números y guiones.">
            <Input
              value={slug}
              onChange={(event) => {
                setSlugTouched(true);
                setSlug(slugify(event.target.value));
              }}
              placeholder="mi-empresa"
              maxLength={100}
              required
            />
          </FormField>
        </div>
        <FormField label="Nombre completo" required>
          <Input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Nombre y apellidos"
            autoComplete="name"
            required
          />
        </FormField>
        <FormField label="Correo del administrador" required>
          <Input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="admin@organizacion.com"
            autoComplete="email"
            required
          />
        </FormField>
        <FormField label="Contraseña" required>
          <PasswordInput
            value={password}
            onChange={setPassword}
            placeholder="Cree una contraseña robusta"
            autoComplete="new-password"
          />
        </FormField>
        <div className="grid gap-1.5">
          {checks.map((check) => (
            <div key={check.label} className="flex items-center gap-2 text-[11px]">
              <span
                className={clsx(
                  "flex h-4 w-4 items-center justify-center rounded-full border",
                  check.ok
                    ? "border-emerald-200 bg-emerald-50 text-emerald-600"
                    : "border-slate-200 bg-slate-50 text-slate-300",
                )}
              >
                <Check className="h-2.5 w-2.5" />
              </span>
              <span className={check.ok ? "text-slate-600" : "text-slate-400"}>{check.label}</span>
            </div>
          ))}
        </div>
        <FormField label="Confirmar contraseña" required error={confirm && confirm !== password ? "Las contraseñas no coinciden." : undefined}>
          <PasswordInput value={confirm} onChange={setConfirm} autoComplete="new-password" placeholder="Repita la contraseña" />
        </FormField>
        <Button type="submit" variant="accent" className="w-full" loading={loading} icon={<ArrowRight className="h-4 w-4" />}>
          Crear organización y acceder
        </Button>
      </form>
      <p className="mt-5 text-center text-[10px] leading-5 text-slate-400">
        La contraseña se almacena con bcrypt. No se envían credenciales por correo ni se generan claves
        por defecto.
      </p>
    </AuthLayout>
  );
}

export function ChangePasswordPage({ forced = false }: { forced?: boolean }) {
  const { logout, user } = useAuth();
  const { notify } = useToast();
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const checks = useMemo(() => passwordChecks(password, user?.email ?? ""), [password, user]);
  const valid = checks.every((check) => check.ok) && password === confirm && current.length > 0;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!valid) {
      setError("Revise los requisitos de la nueva contraseña.");
      return;
    }
    setLoading(true);
    try {
      await authApi.changePassword({ current_password: current, new_password: password });
      notify({
        tone: "success",
        title: "Contraseña actualizada",
        message: "Todas las sesiones fueron revocadas. Inicie sesión nuevamente.",
      });
      await logout();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No fue posible actualizar la contraseña.");
    } finally {
      setLoading(false);
    }
  }

  const content = (
    <div className={clsx("w-full", forced ? "max-w-md" : "max-w-xl")}>
      <div className="mb-7">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-100 bg-cyan-50 text-accent-700">
          <KeyRound className="h-5 w-5" />
        </div>
        <p className="section-kicker">{forced ? "Acción requerida" : "Seguridad de la cuenta"}</p>
        <h1 className="mt-1.5 text-2xl font-bold text-ink-950">Cambiar contraseña</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          {forced
            ? "Un administrador estableció una contraseña temporal. Debe cambiarla antes de continuar."
            : "Al cambiarla se revocarán todas las sesiones activas y deberá iniciar sesión nuevamente."}
        </p>
      </div>
      {error && (
        <Alert tone="danger" className="mb-5" title="No se pudo cambiar">
          {error}
        </Alert>
      )}
      <form onSubmit={onSubmit} className="space-y-4">
        <FormField label="Contraseña actual" required>
          <PasswordInput value={current} onChange={setCurrent} autoComplete="current-password" />
        </FormField>
        <FormField label="Nueva contraseña" required>
          <PasswordInput value={password} onChange={setPassword} autoComplete="new-password" />
        </FormField>
        <div className="grid gap-1.5">
          {checks.map((check) => (
            <div key={check.label} className="flex items-center gap-2 text-[11px]">
              <CheckCircle2 className={clsx("h-3.5 w-3.5", check.ok ? "text-emerald-500" : "text-slate-300")} />
              <span className={check.ok ? "text-slate-600" : "text-slate-400"}>{check.label}</span>
            </div>
          ))}
        </div>
        <FormField
          label="Confirmar nueva contraseña"
          required
          error={confirm && confirm !== password ? "Las contraseñas no coinciden." : undefined}
        >
          <PasswordInput value={confirm} onChange={setConfirm} autoComplete="new-password" />
        </FormField>
        <Button type="submit" className="w-full" loading={loading}>
          Actualizar contraseña
        </Button>
      </form>
    </div>
  );

  if (!forced) return <div className="mx-auto mt-4 max-w-xl rounded-2xl border border-line bg-white p-6 shadow-card sm:p-8">{content}</div>;

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface p-4">
      <div className="w-full max-w-md rounded-2xl border border-line bg-white p-6 shadow-card sm:p-8">
        <Logo size={42} showWordmark className="mb-7" />
        {content}
      </div>
    </div>
  );
}
