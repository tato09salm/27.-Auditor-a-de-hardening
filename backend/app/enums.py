"""Enumeraciones estables del dominio."""

from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ConnectionMethod(StrEnum):
    SSH = "ssh"
    SIMULATED = "simulated"


class AuthMethod(StrEnum):
    KEY = "key"
    PASSWORD = "password"


class ServerStatus(StrEnum):
    PENDING = "pending"
    ONLINE = "online"
    OFFLINE = "offline"
    AUTH_ERROR = "auth_error"
    DISABLED = "disabled"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CheckStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUATED = "not_evaluated"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(StrEnum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    AUTOMATION = "automation"
    RETRY = "retry"


class FindingStatus(StrEnum):
    DETECTED = "detected"
    IN_REVIEW = "in_review"
    CORRECTION_PLANNED = "correction_planned"
    FIXED_PENDING_VALIDATION = "fixed_pending_validation"
    RESOLVED = "resolved"
    RISK_ACCEPTED = "risk_accepted"
    FALSE_POSITIVE = "false_positive"


class RecommendationStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    INVALID = "invalid"


class RecommendationSource(StrEnum):
    AI = "ai"
    REFERENCE = "reference"


class ReportType(StrEnum):
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


class ReportFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"


class LogResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"


ACTIVE_FINDING_STATUSES = (
    FindingStatus.DETECTED.value,
    FindingStatus.IN_REVIEW.value,
    FindingStatus.CORRECTION_PLANNED.value,
    FindingStatus.FIXED_PENDING_VALIDATION.value,
    FindingStatus.RISK_ACCEPTED.value,
)

SEVERITY_ORDER = {
    Severity.CRITICAL.value: 5,
    Severity.HIGH.value: 4,
    Severity.MEDIUM.value: 3,
    Severity.LOW.value: 2,
    Severity.INFO.value: 1,
}
