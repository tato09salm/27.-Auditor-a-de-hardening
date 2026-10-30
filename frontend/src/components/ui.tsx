import clsx from "clsx";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clipboard,
  Copy,
  Loader2,
  Search,
  ShieldAlert,
  X,
  XCircle,
} from "lucide-react";
import {
  forwardRef,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  useEffect,
  useState,
} from "react";
import { createPortal } from "react-dom";
import type { CheckStatus, FindingStatus, RunStatus, Severity } from "../types";
import {
  findingStatusLabel,
  percent,
  runStatusLabel,
  scoreTone,
  severityLabel,
  statusLabel,
} from "../lib/format";

/* -------------------------------------------------------------------------- */
/* Buttons                                                                    */
/* -------------------------------------------------------------------------- */
type ButtonVariant = "primary" | "accent" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
}

const buttonVariants: Record<ButtonVariant, string> = {
  primary: "btn-primary",
  accent: "btn-accent",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
  danger: "btn-danger",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  className,
  children,
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={clsx(buttonVariants[variant], size === "sm" && "btn-sm", className)}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}

/* -------------------------------------------------------------------------- */
/* Badges                                                                     */
/* -------------------------------------------------------------------------- */
type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "accent" | "dark";

const toneClasses: Record<Tone, string> = {
  neutral: "border-slate-200 bg-slate-50 text-slate-600",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
  danger: "border-red-200 bg-red-50 text-red-700",
  info: "border-blue-200 bg-blue-50 text-blue-700",
  accent: "border-cyan-200 bg-cyan-50 text-cyan-700",
  dark: "border-slate-700 bg-slate-800 text-slate-100",
};

export function Badge({
  children,
  tone = "neutral",
  dot = false,
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span className={clsx("badge", toneClasses[tone], className)}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

const severityClasses: Record<Severity, string> = {
  critical: "border-red-200 bg-red-50 text-red-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-blue-200 bg-blue-50 text-blue-700",
  info: "border-slate-200 bg-slate-50 text-slate-600",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={clsx("badge", severityClasses[severity])}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {severityLabel[severity]}
    </span>
  );
}

const checkStatusClasses: Record<CheckStatus, string> = {
  passed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "border-red-200 bg-red-50 text-red-700",
  not_applicable: "border-slate-200 bg-slate-100 text-slate-500",
  not_evaluated: "border-amber-200 bg-amber-50 text-amber-700",
};

export function CheckStatusBadge({ status }: { status: CheckStatus }) {
  return (
    <span className={clsx("badge", checkStatusClasses[status])}>
      {status === "passed" ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : status === "failed" ? (
        <XCircle className="h-3 w-3" />
      ) : status === "not_evaluated" ? (
        <AlertTriangle className="h-3 w-3" />
      ) : (
        <span className="h-1.5 w-1.5 rounded-full bg-current" />
      )}
      {statusLabel[status]}
    </span>
  );
}

const runStatusClasses: Record<RunStatus, string> = {
  queued: "border-slate-200 bg-slate-50 text-slate-600",
  running: "border-cyan-200 bg-cyan-50 text-cyan-700",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "border-red-200 bg-red-50 text-red-700",
  cancelled: "border-slate-200 bg-slate-100 text-slate-500",
};

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return (
    <span className={clsx("badge", runStatusClasses[status])}>
      {status === "running" && <Loader2 className="h-3 w-3 animate-spin" />}
      {status === "completed" && <Check className="h-3 w-3" />}
      {status === "failed" && <XCircle className="h-3 w-3" />}
      {runStatusLabel[status]}
    </span>
  );
}

const findingStatusClasses: Record<FindingStatus, string> = {
  detected: "border-red-200 bg-red-50 text-red-700",
  in_review: "border-amber-200 bg-amber-50 text-amber-700",
  correction_planned: "border-blue-200 bg-blue-50 text-blue-700",
  fixed_pending_validation: "border-cyan-200 bg-cyan-50 text-cyan-700",
  resolved: "border-emerald-200 bg-emerald-50 text-emerald-700",
  risk_accepted: "border-violet-200 bg-violet-50 text-violet-700",
  false_positive: "border-slate-200 bg-slate-100 text-slate-500",
};

export function FindingStatusBadge({ status }: { status: FindingStatus }) {
  return (
    <span className={clsx("badge", findingStatusClasses[status])}>
      {findingStatusLabel[status]}
    </span>
  );
}

export function ServerStatusBadge({ status }: { status: string }) {
  const classes =
    status === "online"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : status === "offline"
        ? "border-red-200 bg-red-50 text-red-700"
        : status === "auth_error"
          ? "border-orange-200 bg-orange-50 text-orange-700"
          : status === "disabled"
            ? "border-slate-200 bg-slate-100 text-slate-500"
            : "border-amber-200 bg-amber-50 text-amber-700";
  return (
    <span className={clsx("badge", classes)}>
      <span
        className={clsx(
          "h-1.5 w-1.5 rounded-full bg-current",
          status === "online" && "shadow-[0_0_0_3px_rgba(5,150,105,0.12)]",
        )}
      />
      {statusLabel[status] ?? status}
    </span>
  );
}

export function RecommendationStatusBadge({ status }: { status: string }) {
  const map: Record<string, { classes: string; label: string }> = {
    pending_review: { classes: "border-amber-200 bg-amber-50 text-amber-700", label: "Pendiente de revisión" },
    approved: { classes: "border-emerald-200 bg-emerald-50 text-emerald-700", label: "Aprobada" },
    rejected: { classes: "border-red-200 bg-red-50 text-red-700", label: "Rechazada" },
    superseded: { classes: "border-slate-200 bg-slate-100 text-slate-500", label: "Reemplazada" },
    invalid: { classes: "border-slate-200 bg-slate-100 text-slate-500", label: "Inválida" },
  };
  const item = map[status] ?? { classes: toneClasses.neutral, label: status };
  return <span className={clsx("badge", item.classes)}>{item.label}</span>;
}

/* -------------------------------------------------------------------------- */
/* Score                                                                      */
/* -------------------------------------------------------------------------- */
const scoreColors = {
  good: "#059669",
  warn: "#d97706",
  bad: "#dc2626",
  empty: "#94a3b8",
};

export function ScoreRing({
  score,
  size = 132,
  label = "Cumplimiento",
  strokeWidth = 9,
}: {
  score: number | null;
  size?: number;
  label?: string;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const value = Math.max(0, Math.min(100, score ?? 0));
  const tone = scoreTone(score);
  const offset = circumference - (value / 100) * circumference;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden="true">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e8edf4"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={scoreColors[tone]}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={score === null ? circumference : offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span
          className="text-2xl font-bold tabular-nums tracking-tight"
          style={{ color: scoreColors[tone] }}
        >
          {score === null ? "—" : `${score.toFixed(1)}%`}
        </span>
        <span className="mt-0.5 max-w-[88px] text-[9px] font-bold uppercase tracking-[0.12em] text-slate-400">
          {label}
        </span>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Layout                                                                     */
/* -------------------------------------------------------------------------- */
export function PageHeader({
  kicker,
  title,
  description,
  actions,
}: {
  kicker?: string;
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        {kicker && <p className="section-kicker mb-1.5">{kicker}</p>}
        <h1 className="text-[26px] font-bold leading-tight text-ink-950 sm:text-[30px]">{title}</h1>
        {description && (
          <div className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-500">{description}</div>
        )}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2.5">{actions}</div>}
    </div>
  );
}

export function Card({
  children,
  className,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}) {
  return <Tag className={clsx("card", className)}>{children}</Tag>;
}

export function SectionHeader({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("flex items-start justify-between gap-4", className)}>
      <div>
        <h2 className="section-title">{title}</h2>
        {description && <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Form fields                                                                */
/* -------------------------------------------------------------------------- */
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...rest }, ref) => <input ref={ref} className={clsx("input", className)} {...rest} />,
);
Input.displayName = "Input";

export function FormField({
  label,
  hint,
  error,
  required,
  children,
  className,
}: {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={clsx("block", className)}>
      <span className="label">
        {label}
        {required && <span className="ml-0.5 text-red-500">*</span>}
      </span>
      {children}
      {hint && !error && <span className="mt-1 block text-[11px] leading-4 text-slate-400">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}

export function SearchField({
  value,
  onChange,
  placeholder = "Buscar…",
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <div className={clsx("relative", className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      <input
        className="input pl-9"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
      />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Modal                                                                      */
/* -------------------------------------------------------------------------- */
export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  size = "md",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  if (!open) return null;
  const widths = {
    sm: "max-w-md",
    md: "max-w-xl",
    lg: "max-w-3xl",
    xl: "max-w-5xl",
  };
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-6">
      <div
        className="absolute inset-0 bg-ink-950/55 backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={clsx(
          "relative flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-3xl border border-white/10 bg-white shadow-2xl animate-fade-up sm:rounded-2xl",
          widths[size],
        )}
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4 sm:px-6">
          <div>
            <h2 id="modal-title" className="text-base font-bold text-ink-950">
              {title}
            </h2>
            {description && <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>}
          </div>
          <button className="icon-btn -mr-1 shrink-0" onClick={onClose} aria-label="Cerrar">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="overflow-y-auto px-5 py-5 sm:px-6">{children}</div>
        {footer && (
          <div className="flex flex-wrap items-center justify-end gap-2.5 border-t border-line bg-slate-50/70 px-5 py-3.5 sm:px-6">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}

export function ConfirmModal({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirmar",
  tone = "primary",
  loading = false,
  children,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  tone?: "primary" | "danger";
  loading?: boolean;
  children?: ReactNode;
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={description}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button variant={tone === "danger" ? "danger" : "primary"} onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      {children}
    </Modal>
  );
}

/* -------------------------------------------------------------------------- */
/* States                                                                     */
/* -------------------------------------------------------------------------- */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("flex flex-col items-center justify-center px-6 py-14 text-center", className)}>
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-line bg-slate-50 text-slate-400">
        {icon ?? <Search className="h-5 w-5" />}
      </div>
      <h3 className="text-sm font-bold text-ink-900">{title}</h3>
      {description && <p className="mt-1.5 max-w-md text-xs leading-5 text-slate-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={clsx("h-5 w-5 animate-spin text-accent-600", className)} />;
}

export function PageLoader({ label = "Cargando información…" }: { label?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-line bg-white shadow-card">
        <Spinner />
      </div>
      <p className="text-xs font-medium text-slate-500">{label}</p>
    </div>
  );
}

export function ErrorState({
  title = "No fue posible cargar la información",
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="p-8">
      <div className="mx-auto flex max-w-md flex-col items-center text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50 text-red-600">
          <ShieldAlert className="h-5 w-5" />
        </div>
        <h3 className="text-sm font-bold text-ink-900">{title}</h3>
        {message && <p className="mt-1.5 text-xs leading-5 text-slate-500">{message}</p>}
        {onRetry && (
          <Button variant="secondary" className="mt-5" onClick={onRetry}>
            Reintentar
          </Button>
        )}
      </div>
    </Card>
  );
}

export function TableSkeleton({ rows = 6, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="table-shell">
      <div className="border-b border-line bg-slate-50 px-4 py-3">
        <div className="skeleton h-3 w-32" />
      </div>
      <div className="divide-y divide-line/70">
        {Array.from({ length: rows }).map((_, row) => (
          <div key={row} className="grid gap-4 px-4 py-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
            {Array.from({ length: cols }).map((__, col) => (
              <div key={col} className="skeleton h-3.5" style={{ width: `${55 + ((row + col) % 4) * 12}%` }} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Misc                                                                       */
/* -------------------------------------------------------------------------- */
export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-line px-4 py-3 sm:flex-row">
      <p className="text-xs text-slate-500">
        Mostrando <span className="font-semibold text-slate-700">{start}</span>–
        <span className="font-semibold text-slate-700">{end}</span> de{" "}
        <span className="font-semibold text-slate-700">{total}</span>
      </p>
      <div className="flex items-center gap-2">
        <button
          className="icon-btn disabled:cursor-not-allowed disabled:opacity-40"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Página anterior"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="min-w-[70px] text-center text-xs font-semibold text-slate-600">
          {page} / {pages}
        </span>
        <button
          className="icon-btn disabled:cursor-not-allowed disabled:opacity-40"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
          aria-label="Página siguiente"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export function CopyButton({ value, label = "Copiar" }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="btn-secondary btn-sm"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1600);
        } catch {
          setCopied(false);
        }
      }}
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copiado" : label}
    </button>
  );
}

export function InlineCode({ children }: { children: ReactNode }) {
  return (
    <code className="rounded-md border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-[11px] text-slate-700">
      {children}
    </code>
  );
}

export function KeyValue({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-ink-900">{children}</dd>
    </div>
  );
}

export function StatDelta({ value }: { value: number | null }) {
  if (value === null || Number.isNaN(value)) return <span className="text-xs text-slate-400">Sin comparación</span>;
  const positive = value >= 0;
  return (
    <span className={clsx("text-xs font-semibold", positive ? "text-emerald-600" : "text-red-600")}>
      {positive ? "+" : ""}
      {value.toFixed(1)} pp
    </span>
  );
}

export function ScoreBar({ score, className }: { score: number | null; className?: string }) {
  const tone = scoreTone(score);
  const colors = { good: "bg-emerald-500", warn: "bg-amber-500", bad: "bg-red-500", empty: "bg-slate-300" };
  return (
    <div className={clsx("h-1.5 w-full overflow-hidden rounded-full bg-slate-100", className)}>
      <div
        className={clsx("h-full rounded-full transition-all duration-500", colors[tone])}
        style={{ width: `${Math.max(0, Math.min(100, score ?? 0))}%` }}
      />
    </div>
  );
}

export function ScoreLabel({ score }: { score: number | null }) {
  if (score === null) return <span className="text-sm text-slate-400">—</span>;
  const tone = scoreTone(score);
  return (
    <span
      className={clsx(
        "text-sm font-bold tabular-nums",
        tone === "good" && "text-emerald-600",
        tone === "warn" && "text-amber-600",
        tone === "bad" && "text-red-600",
      )}
    >
      {percent(score)}
    </span>
  );
}

export function EvidenceValue({ value }: { value: unknown }) {
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return (
    <div className="relative">
      <pre className="mono-block max-h-72 whitespace-pre-wrap break-words">{text}</pre>
      <div className="absolute right-2 top-2">
        <CopyButton value={text} label="" />
      </div>
    </div>
  );
}

export function Alert({
  tone = "info",
  title,
  children,
  className,
}: {
  tone?: "info" | "warning" | "danger" | "success";
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  const classes = {
    info: "border-blue-200 bg-blue-50/70 text-blue-900",
    warning: "border-amber-200 bg-amber-50/75 text-amber-900",
    danger: "border-red-200 bg-red-50/75 text-red-900",
    success: "border-emerald-200 bg-emerald-50/75 text-emerald-900",
  };
  const Icon = tone === "danger" ? XCircle : tone === "success" ? CheckCircle2 : AlertTriangle;
  return (
    <div className={clsx("rounded-xl border p-3.5", classes[tone], className)}>
      <div className="flex gap-2.5">
        <Icon className="mt-0.5 h-4 w-4 shrink-0" />
        <div className="min-w-0 text-xs leading-5">
          {title && <p className="font-bold">{title}</p>}
          <div className={clsx(title && "mt-0.5", "opacity-90")}>{children}</div>
        </div>
      </div>
    </div>
  );
}

export function ClipboardIcon() {
  return <Clipboard className="h-4 w-4" />;
}
