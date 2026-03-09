"""API endpoints for group management."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate
from app.services.group_service import (
    GroupServiceError,
    create_group,
    get_group_by_id,
    update_group,
)

router = APIRouter(prefix="/groups", tags=["groups"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _to_response(group) -> GroupResponse:
    """Convert a Group ORM model to a GroupResponse schema."""
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=len(group.memberships),
        memberships=group.memberships,
    )


@router.post("", status_code=201, response_model=GroupResponse)
async def create_group_endpoint(
    body: GroupCreate,
    db: DbSession,
) -> GroupResponse:
    """Create a new group and assign the creator as the initial member."""
    try:
        group = await create_group(
            db,
            name=body.name,
            description=body.description,
            creator_id=body.creator_id,
        )
    except GroupServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _to_response(group)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_endpoint(
    group_id: uuid.UUID,
    db: DbSession,
) -> GroupResponse:
    """Retrieve a group by its ID."""
    group = await get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found.")
    return _to_response(group)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group_endpoint(
    group_id: uuid.UUID,
    body: GroupUpdate,
    db: DbSession,
) -> GroupResponse:
    """Update a group's name and/or description."""
    try:
        group = await update_group(
            db,
            group_id,
            name=body.name,
            description=body.description,
        )
    except GroupServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _to_response(group)
