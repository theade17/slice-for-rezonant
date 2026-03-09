"""Create group tables.

Revision ID: 001
Revises: None
Create Date: 2026-03-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("user_id", name="uq_one_group_per_user"),
    )
    op.create_index(
        "ix_group_memberships_user_id",
        "group_memberships",
        ["user_id"],
    )

    op.create_table(
        "group_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_id", sa.Uuid(), nullable=True),
        sa.Column("recipient_phone", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "group_id",
            "recipient_id",
            name="uq_one_active_invite_per_recipient",
        ),
    )
    op.create_index(
        "ix_group_invitations_recipient_id",
        "group_invitations",
        ["recipient_id"],
    )


def downgrade() -> None:
    op.drop_table("group_invitations")
    op.drop_table("group_memberships")
    op.drop_table("groups")
