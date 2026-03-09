"""Business logic for group operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.group import Group, GroupMembership

MAX_GROUP_SIZE = settings.max_group_size


class GroupServiceError(Exception):
    """Base exception for group service errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UserAlreadyInGroupError(GroupServiceError):
    """Raised when a user tries to join/create while already in a group."""

    def __init__(self) -> None:
        super().__init__(
            message="User is already a member of a group.",
            status_code=409,
        )


class GroupNotFoundError(GroupServiceError):
    """Raised when a group cannot be found."""

    def __init__(self) -> None:
        super().__init__(
            message="Group not found.",
            status_code=404,
        )


class GroupFullError(GroupServiceError):
    """Raised when a group has reached its maximum member count."""

    def __init__(self) -> None:
        super().__init__(
            message=(f"Group has reached the maximum of {MAX_GROUP_SIZE} members."),
            status_code=409,
        )


async def get_user_membership(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> GroupMembership | None:
    """Return the active membership for a user, or None."""
    result = await db.execute(
        select(GroupMembership).where(GroupMembership.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_group_member_count(
    db: AsyncSession,
    group_id: uuid.UUID,
) -> int:
    """Return the number of members in a group."""
    result = await db.execute(
        select(func.count())
        .select_from(GroupMembership)
        .where(GroupMembership.group_id == group_id)
    )
    return result.scalar_one()


async def create_group(
    db: AsyncSession,
    *,
    name: str,
    description: str | None,
    creator_id: uuid.UUID,
) -> Group:
    """Create a new group and add the creator as the first member.

    Raises:
        UserAlreadyInGroupError: If the creator is already in a group.
    """
    existing = await get_user_membership(db, creator_id)
    if existing is not None:
        raise UserAlreadyInGroupError

    group = Group(name=name, description=description)
    db.add(group)
    await db.flush()

    membership = GroupMembership(user_id=creator_id, group_id=group.id)
    db.add(membership)
    await db.commit()

    # Reload with relationships
    return await get_group_by_id(db, group.id)  # type: ignore[return-value]


async def get_group_by_id(
    db: AsyncSession,
    group_id: uuid.UUID,
) -> Group | None:
    """Fetch a group by ID, including memberships (non-deleted only)."""
    result = await db.execute(
        select(Group)
        .options(selectinload(Group.memberships))
        .where(Group.id == group_id, Group.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def update_group(
    db: AsyncSession,
    group_id: uuid.UUID,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Group:
    """Update a group's metadata.

    Raises:
        GroupNotFoundError: If the group does not exist.
    """
    group = await get_group_by_id(db, group_id)
    if group is None:
        raise GroupNotFoundError

    if name is not None:
        group.name = name
    if description is not None:
        group.description = description

    db.add(group)
    await db.commit()
    await db.refresh(group)

    return await get_group_by_id(db, group_id)  # type: ignore[return-value]
