"""Add natal_charts table

Revision ID: 0003_add_natal_charts
Revises: 0002_add_birth_profiles
Create Date: 2026-09-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_add_natal_charts"
down_revision: Union[str, None] = "0002_add_birth_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "natal_charts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("birth_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("birth_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("astrology_system", sa.String(length=32), nullable=False),
        sa.Column("house_system", sa.String(length=32), nullable=False),
        sa.Column("ayanamsa", sa.String(length=32), nullable=True),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("sun_sign", sa.String(length=32), nullable=False),
        sa.Column("moon_sign", sa.String(length=32), nullable=False),
        sa.Column("ascendant_sign", sa.String(length=32), nullable=False),
        sa.Column("chart_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_natal_charts_user_id", "natal_charts", ["user_id"])
    op.create_index("ix_natal_charts_birth_profile_id", "natal_charts", ["birth_profile_id"])
    op.create_index("ix_natal_charts_user_profile", "natal_charts", ["user_id", "birth_profile_id"])
    op.create_index("ix_natal_charts_system_version", "natal_charts", ["astrology_system", "engine_version"])


def downgrade() -> None:
    op.drop_table("natal_charts")
