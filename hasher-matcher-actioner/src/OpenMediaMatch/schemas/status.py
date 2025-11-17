from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """Response schema for status endpoint."""

    status: str = Field(..., description="Status message")


class SiteMapResponse(BaseModel):
    """Response schema for site map endpoint."""

    routes: list[str] = Field(..., description="List of available routes")
