"""Add birth_profiles table

Revision ID: 0002_add_birth_profiles
Revises: 0001_initial_users
Create Date: 2026-09-06 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_add_birth_profiles"
down_revision: Union[str, None] = "0001_initial_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "birth_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("local_time", sa.Time(), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("utc_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("astrology_system", sa.String(length=20), server_default="western", nullable=False),
        sa.Column("birth_time_accuracy", sa.String(length=20), server_default="exact", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_birth_profiles_user_id", "birth_profiles", ["user_id"])
    op.create_index("ix_birth_profiles_user_primary", "birth_profiles", ["user_id", "is_primary"])


def downgrade() -> None:
    op.drop_index("ix_birth_profiles_user_primary", table_name="birth_profiles")
    op.drop_index("ix_birth_profiles_user_id", table_name="birth_profiles")
    op.drop_table("birth_profiles")
