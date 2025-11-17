"""sample_user_entity

Revision ID: 25b760fbfd74
Revises:
Create Date: 2025-11-17 11:51:44.987361

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "25b760fbfd74"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.String(), nullable=False),
        sa.Column("last_modified_by_user_id", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="sample_schema",
    )
    op.create_index(op.f("ix_sample_schema_user_email"), "user", ["email"], unique=True, schema="sample_schema")
    op.create_index(op.f("ix_sample_schema_user_id"), "user", ["id"], unique=False, schema="sample_schema")
    op.create_index(op.f("ix_sample_schema_user_username"), "user", ["username"], unique=True, schema="sample_schema")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_sample_schema_user_username"), table_name="user", schema="sample_schema")
    op.drop_index(op.f("ix_sample_schema_user_id"), table_name="user", schema="sample_schema")
    op.drop_index(op.f("ix_sample_schema_user_email"), table_name="user", schema="sample_schema")
    op.drop_table("user", schema="sample_schema")
