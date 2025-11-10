from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HashRequest(BaseModel):
    """Request schema for hashing content from URL."""

    url: str = Field(..., description="URL to the media content to hash")
    content_type: Optional[str] = Field(
        None, description="Content type (photo, video, etc.)"
    )
    types: Optional[str] = Field(
        None, description="Comma-separated list of signal types to generate"
    )


class HashResponse(BaseModel):
    """Response schema for hash generation."""

    model_config = ConfigDict(extra="allow")


class HashPostRequest(BaseModel):
    """Request schema for hashing uploaded files."""

    # File uploads are handled separately in flask-openapi3
    pass
