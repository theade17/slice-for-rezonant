"""Tests for the groups API endpoints and business logic."""

import uuid

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# POST /groups
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_group_success(client: AsyncClient, user_id: uuid.UUID):
    """Creating a group returns 201 with group data and creator as member."""
    response = await client.post(
        "/groups",
        json={
            "name": "Family Plan",
            "description": "A family group",
            "creator_id": str(user_id),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Family Plan"
    assert data["description"] == "A family group"
    assert data["member_count"] == 1
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_create_group_user_already_in_group(
    client: AsyncClient, user_id: uuid.UUID
):
    """A user already in a group cannot create another one."""
    # Create the first group
    resp1 = await client.post(
        "/groups",
        json={"name": "Group 1", "creator_id": str(user_id)},
    )
    assert resp1.status_code == 201

    # Attempt to create a second group with the same user
    resp2 = await client.post(
        "/groups",
        json={"name": "Group 2", "creator_id": str(user_id)},
    )
    assert resp2.status_code == 409
    assert "already a member" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_create_group_without_name_fails(client: AsyncClient, user_id: uuid.UUID):
    """Group creation without a name should fail validation."""
    response = await client.post(
        "/groups",
        json={"creator_id": str(user_id)},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_group_without_creator_fails(client: AsyncClient):
    """Group creation without a creator_id should fail validation."""
    response = await client.post(
        "/groups",
        json={"name": "Missing Creator"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_group_minimal_fields(client: AsyncClient, user_id: uuid.UUID):
    """Creating a group with only required fields should succeed."""
    response = await client.post(
        "/groups",
        json={"name": "Minimal Group", "creator_id": str(user_id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Group"
    assert data["description"] is None
    assert data["member_count"] == 1


@pytest.mark.asyncio
async def test_two_different_users_can_create_groups(
    client: AsyncClient,
    user_id: uuid.UUID,
    another_user_id: uuid.UUID,
):
    """Two different users should each be able to create their own group."""
    resp1 = await client.post(
        "/groups",
        json={"name": "Group A", "creator_id": str(user_id)},
    )
    resp2 = await client.post(
        "/groups",
        json={"name": "Group B", "creator_id": str(another_user_id)},
    )

    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] != resp2.json()["id"]


# ---------------------------------------------------------------------------
# GET /groups/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_group_success(client: AsyncClient, user_id: uuid.UUID):
    """Fetching an existing group should return 200 with correct data."""
    create_resp = await client.post(
        "/groups",
        json={
            "name": "Fetch Me",
            "description": "test",
            "creator_id": str(user_id),
        },
    )
    group_id = create_resp.json()["id"]

    response = await client.get(f"/groups/{group_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Fetch Me"
    assert data["description"] == "test"
    assert data["member_count"] == 1


@pytest.mark.asyncio
async def test_get_group_not_found(client: AsyncClient):
    """Fetching a non-existent group should return 404."""
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/groups/{fake_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# PATCH /groups/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_group_name(client: AsyncClient, user_id: uuid.UUID):
    """Updating only the group name should succeed."""
    create_resp = await client.post(
        "/groups",
        json={"name": "Old Name", "creator_id": str(user_id)},
    )
    group_id = create_resp.json()["id"]

    response = await client.patch(
        f"/groups/{group_id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_update_group_description(client: AsyncClient, user_id: uuid.UUID):
    """Updating only the description should succeed."""
    create_resp = await client.post(
        "/groups",
        json={"name": "My Group", "creator_id": str(user_id)},
    )
    group_id = create_resp.json()["id"]

    response = await client.patch(
        f"/groups/{group_id}",
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_group_not_found(client: AsyncClient):
    """Updating a non-existent group should return 404."""
    fake_id = str(uuid.uuid4())
    response = await client.patch(
        f"/groups/{fake_id}",
        json={"name": "No Group"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_group_name_and_description(
    client: AsyncClient, user_id: uuid.UUID
):
    """Updating both name and description in one request should succeed."""
    create_resp = await client.post(
        "/groups",
        json={
            "name": "Original",
            "description": "Original desc",
            "creator_id": str(user_id),
        },
    )
    group_id = create_resp.json()["id"]

    response = await client.patch(
        f"/groups/{group_id}",
        json={"name": "Updated", "description": "New desc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "New desc"


# ---------------------------------------------------------------------------
# Business rule: one group per user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_cannot_be_member_of_more_than_one_group(
    client: AsyncClient,
    user_id: uuid.UUID,
):
    """A user already in a group is rejected when creating a second."""
    # Create first group successfully
    resp1 = await client.post(
        "/groups",
        json={"name": "First", "creator_id": str(user_id)},
    )
    assert resp1.status_code == 201

    # Attempt to create second group – should fail
    resp2 = await client.post(
        "/groups",
        json={"name": "Second", "creator_id": str(user_id)},
    )
    assert resp2.status_code == 409
    assert "already a member" in resp2.json()["detail"]

    # Verify the first group is still intact
    group_id = resp1.json()["id"]
    get_resp = await client.get(f"/groups/{group_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["member_count"] == 1


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """The health endpoint should return 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
