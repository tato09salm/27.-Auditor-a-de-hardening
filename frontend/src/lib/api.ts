import type {
  ApiToken,
  ApiTokenCreated,
  AuditLog,
  AuditRun,
  AuditRunDetail,
  Benchmark,
  ConnectionTestResult,
  Control,
  DashboardData,
  Finding,
  FindingDetail,
  Page,
  Profile,
  ProfileDetail,
  RecommendationDetail,
  Report,
  Schedule,
  Server,
  ServerDetail,
  SetupStatus,
  SystemInfo,
  TokenResponse,
  User,
  UserAdmin,
} from "../types";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

let accessToken: string | null = null;
let onAuthFailure: (() => void) | null = null;
let refreshPromise: Promise<TokenResponse | null> | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAuthFailureHandler(handler: (() => void) | null): void {
  onAuthFailure = handler;
}

export class ApiError extends Error {
  status: number;
  code: string;
  fields?: { field: string; message: string; type: string }[];
  requestId?: string;

  constructor(
    message: string,
    status: number,
    code = "error",
    fields?: { field: string; message: string; type: string }[],
    requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
    this.requestId = requestId;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
}

async function parseError(response: Response): Promise<ApiError> {
  let payload: Record<string, unknown> = {};
  try {
    payload = (await response.json()) as Record<string, unknown>;
  } catch {
    /* respuesta sin JSON */
  }
  const message =
    typeof payload.detail === "string"
      ? payload.detail
      : response.status === 0
        ? "No fue posible contactar el servidor."
        : `La solicitud falló (${response.status}).`;
  return new ApiError(
    message,
    response.status,
    typeof payload.code === "string" ? payload.code : "http_error",
    Array.isArray(payload.fields)
      ? (payload.fields as { field: string; message: string; type: string }[])
      : undefined,
    typeof payload.request_id === "string" ? payload.request_id : undefined,
  );
}

export async function refreshAccessToken(): Promise<TokenResponse | null> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        accessToken = null;
        return null;
      }
      const data = (await response.json()) as TokenResponse;
      accessToken = data.access_token;
      return data;
    } catch {
      accessToken = null;
      return null;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

async function rawRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }
  if (options.auth !== false && accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      body,
      credentials: "include",
    });
  } catch {
    throw new ApiError(
      "No fue posible contactar el servidor. Verifique que el backend esté disponible.",
      0,
      "network_error",
    );
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return (await response.text()) as T;
  return (await response.json()) as T;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const isAuthPath = path.startsWith("/auth/") || path.startsWith("/setup/");
  try {
    return await rawRequest<T>(path, options);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401 && !isAuthPath) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return rawRequest<T>(path, options);
      }
      accessToken = null;
      onAuthFailure?.();
    }
    throw error;
  }
}

export async function downloadReport(report: Report): Promise<void> {
  const headers = new Headers();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  let response = await fetch(`${API_BASE}/reports/${report.id}/download`, {
    headers,
    credentials: "include",
  });
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed && accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
      response = await fetch(`${API_BASE}/reports/${report.id}/download`, {
        headers,
        credentials: "include",
      });
    }
  }
  if (!response.ok) throw await parseError(response);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = report.file_name;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export const authApi = {
  async setupStatus(): Promise<SetupStatus> {
    return rawRequest<SetupStatus>("/setup/status", { auth: false });
  },
  async setup(payload: {
    organization_name: string;
    organization_slug: string;
    admin_full_name: string;
    admin_email: string;
    admin_password: string;
  }): Promise<TokenResponse> {
    const data = await rawRequest<TokenResponse>("/setup/initialize", {
      method: "POST",
      body: payload,
      auth: false,
    });
    accessToken = data.access_token;
    return data;
  },
  async login(payload: { email: string; password: string }): Promise<TokenResponse> {
    const data = await rawRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: payload,
      auth: false,
    });
    accessToken = data.access_token;
    return data;
  },
  async logout(): Promise<void> {
    try {
      await rawRequest("/auth/logout", { method: "POST", auth: false });
    } finally {
      accessToken = null;
    }
  },
  async refresh(): Promise<TokenResponse | null> {
    return refreshAccessToken();
  },
  async me(): Promise<User> {
    return apiRequest<User>("/users/me");
  },
  async changePassword(payload: {
    current_password: string;
    new_password: string;
  }): Promise<{ message: string }> {
    return apiRequest("/auth/change-password", { method: "POST", body: payload });
  },
};

export const dashboardApi = {
  get(params: Record<string, string | undefined>): Promise<DashboardData> {
    return apiRequest(`/dashboard${query(params)}`);
  },
};

export const serversApi = {
  list(params: Record<string, string | number | boolean | undefined> = {}): Promise<Page<Server>> {
    return apiRequest(`/servers${query(params)}`);
  },
  get(id: string): Promise<ServerDetail> {
    return apiRequest(`/servers/${id}`);
  },
  create(payload: Record<string, unknown>): Promise<Server> {
    return apiRequest("/servers", { method: "POST", body: payload });
  },
  update(id: string, payload: Record<string, unknown>): Promise<Server> {
    return apiRequest(`/servers/${id}`, { method: "PATCH", body: payload });
  },
  authorize(
    id: string,
    payload: { confirmed: boolean; allow_private_target: boolean; comment?: string },
  ): Promise<Server> {
    return apiRequest(`/servers/${id}/authorize`, { method: "POST", body: payload });
  },
  setCredential(id: string, secret: string): Promise<Server> {
    return apiRequest(`/servers/${id}/credential`, {
      method: "PUT",
      body: { secret },
    });
  },
  testConnection(id: string): Promise<ConnectionTestResult> {
    return apiRequest(`/servers/${id}/test-connection`, { method: "POST" });
  },
};

export const profilesApi = {
  list(): Promise<Profile[]> {
    return apiRequest("/profiles");
  },
  get(id: string): Promise<ProfileDetail> {
    return apiRequest(`/profiles/${id}`);
  },
  benchmarks(): Promise<Benchmark[]> {
    return apiRequest("/benchmarks");
  },
  controls(benchmarkId: string): Promise<Control[]> {
    return apiRequest(`/benchmarks/${benchmarkId}/controls`);
  },
  create(payload: Record<string, unknown>): Promise<ProfileDetail> {
    return apiRequest("/profiles", { method: "POST", body: payload });
  },
  update(id: string, payload: Record<string, unknown>): Promise<ProfileDetail> {
    return apiRequest(`/profiles/${id}`, { method: "PATCH", body: payload });
  },
};

export const auditsApi = {
  list(params: Record<string, string | number | undefined> = {}): Promise<Page<AuditRun>> {
    return apiRequest(`/audits${query(params)}`);
  },
  get(id: string): Promise<AuditRunDetail> {
    return apiRequest(`/audits/${id}`);
  },
  create(payload: { server_id: string; profile_id?: string }): Promise<AuditRun> {
    return apiRequest("/audits", { method: "POST", body: payload });
  },
};

export const findingsApi = {
  list(params: Record<string, string | number | boolean | undefined> = {}): Promise<Page<Finding>> {
    return apiRequest(`/findings${query(params)}`);
  },
  get(id: string): Promise<FindingDetail> {
    return apiRequest(`/findings/${id}`);
  },
  update(id: string, payload: Record<string, unknown>): Promise<FindingDetail> {
    return apiRequest(`/findings/${id}`, { method: "PATCH", body: payload });
  },
  generateRecommendation(id: string): Promise<{ recommendation: RecommendationDetail; message: string }> {
    return apiRequest(`/findings/${id}/recommendations`, { method: "POST" });
  },
};

export const recommendationsApi = {
  list(
    params: Record<string, string | number | undefined> = {},
  ): Promise<Page<RecommendationDetail>> {
    return apiRequest(`/recommendations${query(params)}`);
  },
  get(id: string): Promise<RecommendationDetail> {
    return apiRequest(`/recommendations/${id}`);
  },
  review(
    id: string,
    payload: { decision: "approved" | "rejected"; comments: string },
  ): Promise<RecommendationDetail> {
    return apiRequest(`/recommendations/${id}/review`, { method: "POST", body: payload });
  },
};

export const reportsApi = {
  list(params: Record<string, string | number | undefined> = {}): Promise<Page<Report>> {
    return apiRequest(`/reports${query(params)}`);
  },
  create(payload: Record<string, unknown>): Promise<Report> {
    return apiRequest("/reports", { method: "POST", body: payload });
  },
};

export const schedulesApi = {
  list(): Promise<Schedule[]> {
    return apiRequest("/schedules");
  },
  create(payload: Record<string, unknown>): Promise<Schedule> {
    return apiRequest("/schedules", { method: "POST", body: payload });
  },
  update(id: string, payload: Record<string, unknown>): Promise<Schedule> {
    return apiRequest(`/schedules/${id}`, { method: "PATCH", body: payload });
  },
  disable(id: string): Promise<{ message: string }> {
    return apiRequest(`/schedules/${id}`, { method: "DELETE" });
  },
};

export const usersApi = {
  list(params: Record<string, string | number | boolean | undefined> = {}): Promise<Page<UserAdmin>> {
    return apiRequest(`/users${query(params)}`);
  },
  roles(): Promise<{ code: string; name: string }[]> {
    return apiRequest("/roles");
  },
  create(payload: Record<string, unknown>): Promise<UserAdmin> {
    return apiRequest("/users", { method: "POST", body: payload });
  },
  update(id: string, payload: Record<string, unknown>): Promise<UserAdmin> {
    return apiRequest(`/users/${id}`, { method: "PATCH", body: payload });
  },
  resetPassword(id: string, payload: Record<string, unknown>): Promise<{ message: string }> {
    return apiRequest(`/users/${id}/reset-password`, { method: "POST", body: payload });
  },
};

export const logsApi = {
  list(params: Record<string, string | number | undefined> = {}): Promise<Page<AuditLog>> {
    return apiRequest(`/audit-logs${query(params)}`);
  },
};

export const settingsApi = {
  get(): Promise<SystemInfo> {
    return apiRequest("/settings");
  },
  tokens(): Promise<ApiToken[]> {
    return apiRequest("/settings/api-tokens");
  },
  createToken(payload: Record<string, unknown>): Promise<ApiTokenCreated> {
    return apiRequest("/settings/api-tokens", { method: "POST", body: payload });
  },
  revokeToken(id: string): Promise<{ message: string }> {
    return apiRequest(`/settings/api-tokens/${id}`, { method: "DELETE" });
  },
};

function query(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "" && value !== null) search.set(key, String(value));
  }
  const serialized = search.toString();
  return serialized ? `?${serialized}` : "";
}
