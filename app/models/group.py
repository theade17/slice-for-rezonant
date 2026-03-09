"""SQLAlchemy models for the groups feature."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class InvitationStatus(enum.StrEnum):
    """Status values for group invitations."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Group(Base):
    """Represents a discount group."""

    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=_new_uuid,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    memberships: Mapped[list["GroupMembership"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list["GroupInvitation"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )


class GroupMembership(Base):
    """Maps a user to a group. A user may belong to at most one group."""

    __tablename__ = "group_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_one_group_per_user"),
        Index("ix_group_memberships_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=_new_uuid,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    group: Mapped["Group"] = relationship(back_populates="memberships")


class GroupInvitation(Base):
    """Tracks invitations sent to join a group."""

    __tablename__ = "group_invitations"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "recipient_id",
            name="uq_one_active_invite_per_recipient",
        ),
        Index("ix_group_invitations_recipient_id", "recipient_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=_new_uuid,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    recipient_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, native_enum=False, length=20),
        default=InvitationStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    group: Mapped["Group"] = relationship(back_populates="invitations")
