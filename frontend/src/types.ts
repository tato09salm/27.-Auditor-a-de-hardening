export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type CheckStatus = "passed" | "failed" | "not_applicable" | "not_evaluated";
export type RunStatus = "queued" | "running" | "completed" | "failed" | "cancelled";
export type FindingStatus =
  | "detected"
  | "in_review"
  | "correction_planned"
  | "fixed_pending_validation"
  | "resolved"
  | "risk_accepted"
  | "false_positive";
export type RecommendationStatus =
  | "pending_review"
  | "approved"
  | "rejected"
  | "superseded"
  | "invalid";
export type Environment = "development" | "staging" | "production";
export type ServerStatus = "pending" | "online" | "offline" | "auth_error" | "disabled";
export type ConnectionMethod = "ssh" | "simulated";
export type AuthMethod = "key" | "password";

export interface Role {
  code: string;
  name: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  must_change_password: boolean;
  last_login_at: string | null;
  created_at: string;
  roles: Role[];
  permissions: string[];
  organization_id: string;
  organization_name: string | null;
}

export interface UserAdmin extends User {
  failed_login_attempts: number;
  locked_until: string | null;
}

export interface SetupStatus {
  initialized: boolean;
  organization_name: string | null;
  product_name: string;
  version: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
}

export interface Server {
  id: string;
  name: string;
  hostname: string;
  ip_address: string;
  os_family: string;
  os_version: string;
  environment: Environment;
  owner_area: string | null;
  connection_method: ConnectionMethod;
  port: number;
  username: string | null;
  auth_method: AuthMethod;
  host_key_fingerprint: string | null;
  default_profile_id: string | null;
  status: ServerStatus;
  connectivity_status: string | null;
  last_connectivity_check_at: string | null;
  last_audit_at: string | null;
  is_active: boolean;
  is_simulated: boolean;
  authorization_confirmed: boolean;
  authorized_at: string | null;
  allow_private_target: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
  credential_configured: boolean;
  credential_updated_at: string | null;
  default_profile_name: string | null;
  last_score: number | null;
  active_findings: number;
}

export interface ServerDetail extends Server {
  total_audits: number;
  last_run_id: string | null;
  open_findings_by_severity: Record<Severity, number>;
}

export interface ConnectionTestResult {
  reachable: boolean;
  message: string;
  status: ServerStatus;
  latency_ms: number | null;
  host_identity_verified: boolean;
  simulated: boolean;
  tested_at: string;
}

export interface Benchmark {
  id: string;
  name: string;
  version: string;
  os_family: string;
  description: string | null;
  source_url: string | null;
  is_official: boolean;
  mapping_status: string;
}

export interface Control {
  id: string;
  benchmark_id: string;
  code: string;
  cis_reference: string | null;
  title: string;
  description: string;
  rationale: string | null;
  severity: Severity;
  category: string;
  cis_level: string | null;
  automated: boolean;
  check_key: string;
  config: Record<string, unknown>;
  remediation_guidance: string;
  references: { title: string; url: string }[];
  is_official_mapping: boolean;
  mapping_notes: string | null;
  is_active: boolean;
  enabled: boolean | null;
}

export interface Profile {
  id: string;
  organization_id: string;
  benchmark_id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  benchmark_name: string | null;
  benchmark_version: string | null;
  control_count: number;
  enabled_control_count: number;
}

export interface ProfileDetail extends Profile {
  controls: Control[];
}

export interface Check {
  id: string;
  control_id: string;
  status: CheckStatus;
  severity: Severity;
  observed_value: string | null;
  evidence: Record<string, unknown>;
  command_executed: string | null;
  duration_ms: number | null;
  error_message: string | null;
  evaluated_at: string | null;
  control_code: string;
  cis_reference: string | null;
  control_title: string;
  category: string;
  remediation_guidance: string;
  is_official_mapping: boolean;
  mapping_notes: string | null;
}

export interface AuditRun {
  id: string;
  organization_id: string;
  server_id: string;
  profile_id: string;
  benchmark_id: string;
  benchmark_version: string;
  status: RunStatus;
  trigger_type: string;
  started_at: string | null;
  finished_at: string | null;
  total_controls: number;
  applicable_count: number;
  passed_count: number;
  failed_count: number;
  not_applicable_count: number;
  not_evaluated_count: number;
  score: number | null;
  summary: Record<string, unknown>;
  error_message: string | null;
  is_simulated: boolean;
  created_at: string;
  server_name: string | null;
  server_hostname: string | null;
  profile_name: string | null;
  triggered_by_name: string | null;
}

export interface AuditRunDetail extends AuditRun {
  checks: Check[];
  findings_created: number;
  findings_resolved: number;
}

export interface Schedule {
  id: string;
  organization_id: string;
  name: string;
  server_id: string;
  profile_id: string;
  cron_expression: string;
  timezone: string;
  is_enabled: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  last_run_id: string | null;
  created_at: string;
  updated_at: string;
  server_name: string | null;
  profile_name: string | null;
}

export interface Finding {
  id: string;
  organization_id: string;
  server_id: string;
  control_id: string;
  first_seen_run_id: string;
  last_seen_run_id: string;
  resolved_by_run_id: string | null;
  status: FindingStatus;
  severity: Severity;
  priority: number;
  title: string;
  description: string;
  owner_id: string | null;
  due_date: string | null;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
  resolution_note: string | null;
  risk_acceptance_until: string | null;
  occurrence_count: number;
  created_at: string;
  updated_at: string;
  server_name: string | null;
  control_code: string | null;
  cis_reference: string | null;
  category: string | null;
  owner_name: string | null;
  recommendation_count: number;
  latest_recommendation_id: string | null;
  latest_recommendation_status: RecommendationStatus | null;
}

export interface FindingEvent {
  id: string;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  comment: string | null;
  actor_id: string | null;
  created_at: string;
  actor_name: string | null;
}

export interface FindingDetail extends Finding {
  evidence: Record<string, unknown>;
  observed_value: string | null;
  events: FindingEvent[];
}

export interface RecommendationPayload {
  problem: string;
  risk: string;
  recommendation: string;
  commands: { command: string; explanation: string; risk?: string | null }[];
  impact: string;
  prerequisites: string[];
  service_interruption_risk: "low" | "medium" | "high" | "unknown";
  validation: string[];
  rollback: string[];
  references: string[];
  confidence: number;
  insufficient_information: boolean;
}

export interface Recommendation {
  id: string;
  organization_id: string;
  finding_id: string;
  check_id: string | null;
  source: "ai" | "reference";
  provider: string;
  model: string;
  status: RecommendationStatus;
  payload: RecommendationPayload;
  confidence: number | null;
  validation_status: string;
  validation_warnings: string[];
  flagged_commands: {
    command: string;
    pattern: string;
    severity: string;
    reason: string;
  }[];
  created_by_id: string | null;
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  created_at: string;
  updated_at: string;
  created_by_name: string | null;
  reviewed_by_name: string | null;
  finding_title?: string | null;
  server_name?: string | null;
  control_code?: string | null;
}

export interface RecommendationReview {
  id: string;
  recommendation_id: string;
  reviewer_id: string | null;
  decision: string;
  comments: string;
  created_at: string;
  reviewer_name: string | null;
}

export interface RecommendationDetail extends Recommendation {
  reviews: RecommendationReview[];
  finding_title: string | null;
  server_name: string | null;
  control_code: string | null;
}

export interface Report {
  id: string;
  organization_id: string;
  report_type: "technical" | "executive";
  format: "pdf" | "docx" | "xlsx";
  server_id: string | null;
  audit_run_id: string | null;
  period_start: string | null;
  period_end: string | null;
  parameters: Record<string, unknown>;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  generated_by_id: string | null;
  created_at: string;
  download_url: string | null;
  server_name: string | null;
  generated_by_name: string | null;
}

export interface DashboardData {
  summary: {
    total_servers: number;
    active_servers: number;
    audited_servers: number;
    pending_servers: number;
    average_score: number | null;
    evaluation_coverage: number;
    findings_critical: number;
    findings_high: number;
    findings_medium: number;
    findings_low: number;
    findings_info: number;
    audits_in_period: number;
    pending_recommendations: number;
    last_audit_at: string | null;
  };
  trend: { period: string; average_score: number | null; audits: number }[];
  top_failures: {
    control_id: string;
    control_code: string;
    cis_reference: string | null;
    title: string;
    severity: Severity;
    failure_count: number;
    affected_servers: number;
  }[];
  recent_runs: {
    id: string;
    server_id: string;
    server_name: string;
    status: RunStatus;
    score: number | null;
    failed_count: number;
    created_at: string;
    is_simulated: boolean;
  }[];
  riskiest_servers: {
    id: string;
    name: string;
    hostname: string;
    environment: Environment;
    score: number | null;
    critical_findings: number;
    high_findings: number;
    last_audit_at: string | null;
    status: ServerStatus;
  }[];
  generated_at: string;
  filters: Record<string, string | null>;
}

export interface AuditLog {
  id: number;
  organization_id: string | null;
  user_id: string | null;
  api_token_id: string | null;
  action: string;
  module: string;
  resource_type: string | null;
  resource_id: string | null;
  result: "success" | "failure" | "denied";
  ip_address: string | null;
  request_id: string | null;
  user_agent: string | null;
  changes: Record<string, unknown>;
  created_at: string;
  user_name: string | null;
}

export interface ApiToken {
  id: string;
  name: string;
  token_prefix: string;
  scopes: string[];
  expires_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface ApiTokenCreated extends ApiToken {
  token: string;
  warning: string;
}

export interface SystemInfo {
  product: string;
  version: string;
  environment: string;
  ai: {
    enabled: boolean;
    available: boolean;
    model: string;
    model_installed?: boolean;
    models?: string[];
    detail?: string;
    error_type?: string;
  };
  simulated_connector_enabled: boolean;
  private_targets_enabled: boolean;
  reports_storage: string;
  audit_max_concurrent_runs: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
