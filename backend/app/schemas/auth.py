from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.security import PasswordPolicyError, validate_password_strength
from app.schemas.common import ORMModel

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SetupStatus(BaseModel):
    initialized: bool
    organization_name: str | None = None
    product_name: str
    version: str


class SetupRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=200)
    organization_slug: str = Field(min_length=2, max_length=100)
    admin_full_name: str = Field(min_length=2, max_length=200)
    admin_email: EmailStr
    admin_password: str = Field(min_length=12, max_length=128)

    @field_validator("organization_slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not SLUG_RE.match(value):
            raise ValueError("El identificador solo admite minúsculas, números y guiones.")
        return value

    @field_validator("admin_password")
    @classmethod
    def validate_password(cls, value: str, info):
        email = info.data.get("admin_email")
        try:
            validate_password_strength(value, email=str(email) if email else None)
        except PasswordPolicyError as exc:
            raise ValueError(str(exc)) from exc
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RoleOut(ORMModel):
    code: str
    name: str


class UserOut(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    roles: list[RoleOut]
    permissions: list[str] = Field(default_factory=list)
    organization_id: UUID
    organization_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        try:
            validate_password_strength(value)
        except PasswordPolicyError as exc:
            raise ValueError(str(exc)) from exc
        return value


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)
    role_codes: list[str] = Field(min_length=1, max_length=4)
    must_change_password: bool = True

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str, info):
        email = info.data.get("email")
        try:
            validate_password_strength(value, str(email) if email else None)
        except PasswordPolicyError as exc:
            raise ValueError(str(exc)) from exc
        return value

    @field_validator("role_codes")
    @classmethod
    def dedupe_roles(cls, value: list[str]) -> list[str]:
        return sorted(set(value))


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    is_active: bool | None = None
    role_codes: list[str] | None = Field(default=None, min_length=1, max_length=4)

    @field_validator("role_codes")
    @classmethod
    def dedupe_roles(cls, value: list[str] | None) -> list[str] | None:
        return sorted(set(value)) if value else value


class UserAdminOut(UserOut):
    failed_login_attempts: int = 0
    locked_until: datetime | None = None


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=12, max_length=128)
    must_change_password: bool = True

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        try:
            validate_password_strength(value)
        except PasswordPolicyError as exc:
            raise ValueError(str(exc)) from exc
        return value


class OrganizationOut(ORMModel):
    id: UUID
    name: str
    slug: str


class ApiTokenCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    scopes: list[str] = Field(default_factory=lambda: ["automation:execute"], min_length=1)
    expires_in_days: int = Field(default=365, ge=1, le=730)

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, value: list[str]) -> list[str]:
        allowed = {
            "automation:execute",
            "automation:recommendations",
            "automation:reports",
        }
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"Alcances no permitidos: {', '.join(sorted(unknown))}")
        return sorted(set(value))


class ApiTokenOut(ORMModel):
    id: UUID
    name: str
    token_prefix: str
    scopes: list[str]
    expires_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ApiTokenCreated(ApiTokenOut):
    token: str
    warning: str = "Guarde este token ahora. No se volverá a mostrar."
