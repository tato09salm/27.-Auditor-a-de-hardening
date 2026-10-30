"""Política anti-SSRF para objetivos de auditoría.

Nunca se resuelven nombres para decidir el destino: se conecta exclusivamente a la
IP validada que el administrador registró. Loopback, link-local, multicast y
metadatos cloud están siempre bloqueados. Las redes privadas requieren tres
condiciones: habilitación global, autorización explícita del servidor y, si se
configuró, pertenencia a AUDIT_ALLOWED_CIDRS.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from app.config import settings
from app.models import Server

METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("100.100.100.200"),
    ipaddress.ip_address("192.0.0.192"),
}


class TargetNotAllowedError(Exception):
    pass


@dataclass(frozen=True)
class TargetDecision:
    address: ipaddress.IPv4Address | ipaddress.IPv6Address
    is_private: bool


def validate_audit_target(server: Server) -> TargetDecision:
    if not server.authorization_confirmed:
        raise TargetNotAllowedError(
            "El servidor no tiene autorización explícita para ser auditado."
        )
    try:
        address = ipaddress.ip_address(server.ip_address)
    except ValueError as exc:
        raise TargetNotAllowedError("La dirección del servidor no es válida.") from exc

    if (
        address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
        or address in METADATA_IPS
    ):
        raise TargetNotAllowedError(
            "El objetivo está bloqueado por la política anti-SSRF (loopback, "
            "link-local, reservado o metadatos cloud)."
        )

    if settings.allowed_cidrs and not any(address in network for network in settings.allowed_cidrs):
        raise TargetNotAllowedError(
            "El objetivo no pertenece a las redes autorizadas en AUDIT_ALLOWED_CIDRS."
        )

    is_private = address.is_private
    if is_private:
        if not settings.audit_allow_private_targets:
            raise TargetNotAllowedError(
                "Las auditorías a redes privadas están deshabilitadas globalmente "
                "(AUDIT_ALLOW_PRIVATE_TARGETS=false)."
            )
        if not server.allow_private_target:
            raise TargetNotAllowedError(
                "El servidor no tiene habilitada la auditoría de objetivo privado."
            )
    return TargetDecision(address=address, is_private=is_private)
