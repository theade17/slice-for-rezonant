"""Pydantic schemas for group API request/response validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GroupCreate(BaseModel):
    """Request body for creating a new group."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    creator_id: uuid.UUID


class GroupUpdate(BaseModel):
    """Request body for updating group metadata."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class MembershipResponse(BaseModel):
    """Membership info included in group responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime


class GroupResponse(BaseModel):
    """Response body for a group."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    member_count: int
    memberships: list[MembershipResponse]


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
