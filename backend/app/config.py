"""Configuración central de CIS Hardening Auditor.

Todos los secretos se reciben por variables de entorno. La aplicación falla al
arrancar si la clave JWT o la clave de cifrado de credenciales no son seguras.
"""

from __future__ import annotations

import base64
import ipaddress
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from cryptography.fernet import Fernet
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "CIS Hardening Auditor"
    app_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    trusted_proxy_ips: str = ""

    # Base de datos
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "27auditoria"
    db_user: str = "postgres"
    db_password: str = Field(default="", repr=False)
    database_url_override: str | None = Field(default=None, repr=False)
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # Autenticación
    secret_key: str = Field(default="", repr=False)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    refresh_cookie_name: str = "cis_refresh"
    cookie_secure: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15
    login_rate_window_seconds: int = 300
    login_rate_max_requests: int = 10
    password_min_length: int = 12

    # Cifrado de credenciales SSH (Fernet, base64 url-safe de 32 bytes)
    fernet_key: str = Field(default="", repr=False)

    # Auditoría / red
    audit_allow_private_targets: bool = False
    audit_allowed_cidrs: str = ""
    ssh_connect_timeout_seconds: int = 10
    ssh_command_timeout_seconds: int = 20
    ssh_max_output_bytes: int = 262_144
    audit_max_concurrent_runs: int = 2
    enable_simulated_connector: bool = False
    artifact_storage_dir: str = "generated"

    # IA opcional
    ai_enabled: bool = True
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: int = 120
    ai_max_evidence_chars: int = 8_000

    # Reportes
    reports_max_period_days: int = 366
    max_page_size: int = 200

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "SECRET_KEY debe tener al menos 32 caracteres. Genere una clave aleatoria."
            )
        return value

    @field_validator("fernet_key")
    @classmethod
    def validate_fernet_key(cls, value: str) -> str:
        if not value:
            raise ValueError("FERNET_KEY es obligatoria para cifrar credenciales.")
        try:
            key = value.encode() if isinstance(value, str) else value
            raw = base64.urlsafe_b64decode(key)
            Fernet(key)
            if len(raw) != 32:
                raise ValueError
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                "FERNET_KEY inválida. Genere una con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            ) from exc
        return value

    @model_validator(mode="after")
    def validate_production_defaults(self) -> "Settings":
        if self.environment == "production":
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE debe ser true en producción.")
            if "*" in self.cors_origin_list:
                raise ValueError("CORS_ORIGINS no puede contener '*' en producción.")
            if self.enable_simulated_connector:
                raise ValueError("ENABLE_SIMULATED_CONNECTOR no puede estar activo en producción.")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("SameSite=None requiere COOKIE_SECURE=true.")
        return self

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        password = quote_plus(self.db_password)
        user = quote_plus(self.db_user)
        return (
            f"postgresql+psycopg://{user}:{password}@{self.db_host}:{self.db_port}/"
            f"{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_proxy_list(self) -> list[str]:
        return [item.strip() for item in self.trusted_proxy_ips.split(",") if item.strip()]

    @property
    def allowed_cidrs(self) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        result = []
        for item in self.audit_allowed_cidrs.split(","):
            item = item.strip()
            if not item:
                continue
            result.append(ipaddress.ip_network(item, strict=False))
        return result

    @property
    def reports_path(self) -> Path:
        # Relativo al directorio backend/ (padre de app/)
        base = Path(__file__).resolve().parents[1]
        path = Path(self.artifact_storage_dir)
        return path if path.is_absolute() else base / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
