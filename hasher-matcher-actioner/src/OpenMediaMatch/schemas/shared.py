# Copyright (c) Meta Platforms, Inc. and affiliates.

from typing import Annotated, Optional

from pydantic import BaseModel, Field

MEDIA_URL_DESCRIPTION = (
    "URL to the media content to hash. Accepts http(s):// URLs and "
    "s3://bucket/key URLs (the latter requires the optional 's3' extra)."
)

# Field aliases for a `url` whose content is fetched and hashed. Reused by every
# request schema that feeds OpenMediaMatch.blueprints.hashing.hash_url_content
# so the accepted schemes stay documented in one place.
MediaUrl = Annotated[str, Field(description=MEDIA_URL_DESCRIPTION)]
OptionalMediaUrl = Annotated[Optional[str], Field(description=MEDIA_URL_DESCRIPTION)]


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standard success response schema."""

    message: str = Field(..., description="Success message")
