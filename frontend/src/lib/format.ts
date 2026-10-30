import type { FindingStatus, RunStatus, Severity } from "../types";

export const severityLabel: Record<Severity, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Media",
  low: "Baja",
  info: "Informativa",
};

export const severityOrder: Severity[] = ["critical", "high", "medium", "low", "info"];

export const findingStatusLabel: Record<FindingStatus, string> = {
  detected: "Detectado",
  in_review: "En revisión",
  correction_planned: "Corrección planificada",
  fixed_pending_validation: "Corregido pendiente de validación",
  resolved: "Resuelto",
  risk_accepted: "Riesgo aceptado",
  false_positive: "Falso positivo",
};

export const runStatusLabel: Record<RunStatus, string> = {
  queued: "En cola",
  running: "Ejecutando",
  completed: "Completada",
  failed: "Fallida",
  cancelled: "Cancelada",
};

export const statusLabel: Record<string, string> = {
  passed: "Aprobado",
  failed: "Incumplido",
  not_applicable: "No aplica",
  not_evaluated: "No evaluado",
  online: "En línea",
  offline: "Sin conexión",
  pending: "Pendiente",
  auth_error: "Error de autenticación",
  disabled: "Desactivado",
  pending_review: "Pendiente de revisión",
  approved: "Aprobada",
  rejected: "Rechazada",
  superseded: "Reemplazada",
  invalid: "Inválida",
  success: "Éxito",
  failure: "Fallo",
  denied: "Denegado",
  technical: "Técnico",
  executive: "Ejecutivo",
  low_risk: "Bajo",
};

export const environmentLabel: Record<string, string> = {
  development: "Desarrollo",
  staging: "Pruebas",
  production: "Producción",
};

export function dateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function shortDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-PE", { dateStyle: "medium" }).format(date);
}

export function relativeTime(value: string | null | undefined): string {
  if (!value) return "sin datos";
  const date = new Date(value).getTime();
  const diff = Date.now() - date;
  const minutes = Math.round(diff / 60000);
  if (Math.abs(minutes) < 1) return "hace instantes";
  if (Math.abs(minutes) < 60) return `hace ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return `hace ${hours} h`;
  const days = Math.round(hours / 24);
  if (Math.abs(days) < 30) return `hace ${days} d`;
  return shortDate(value);
}

export function percent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(decimals)}%`;
}

export function number(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("es-PE").format(value);
}

export function bytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function scoreTone(score: number | null | undefined): "good" | "warn" | "bad" | "empty" {
  if (score === null || score === undefined) return "empty";
  if (score >= 80) return "good";
  if (score >= 60) return "warn";
  return "bad";
}

export function truncate(value: string, length = 120): string {
  if (value.length <= length) return value;
  return `${value.slice(0, length)}…`;
}

export function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
