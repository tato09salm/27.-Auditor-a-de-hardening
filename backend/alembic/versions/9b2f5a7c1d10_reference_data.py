"""Seed de permisos, roles y catálogo CIS inicial

Revision ID: 9b2f5a7c1d10
Revises: c8f949a9645c
Create Date: 2026-10-29

Los identificadores CIS fueron contrastados con el PDF oficial del benchmark
CIS Ubuntu Linux 22.04 LTS v1.0.0. Los controles internos están marcados como
tales en ``is_official_mapping`` y ``mapping_notes``.
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session

from app.reference_data import seed_reference_data

revision: str = "9b2f5a7c1d10"
down_revision: Union[str, None] = "c8f949a9645c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        seed_reference_data(session)
        session.commit()
    finally:
        session.close()


def downgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("DELETE FROM role_permissions")
    bind.exec_driver_sql("DELETE FROM user_roles")
    bind.exec_driver_sql("DELETE FROM permissions")
    bind.exec_driver_sql("DELETE FROM roles")
    bind.exec_driver_sql(
        "DELETE FROM cis_benchmarks WHERE name = 'CIS Ubuntu Linux 22.04 LTS Benchmark' "
        "AND version = '1.0.0' AND os_family = 'ubuntu'"
    )
