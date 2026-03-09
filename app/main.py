"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routers.groups import router as groups_router

app = FastAPI(
    title="Slice Mobile Groups API",
    description="Backend API for the Slice Mobile group discount feature.",
    version="0.1.0",
)

app.include_router(groups_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
