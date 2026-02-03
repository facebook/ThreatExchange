from typing import Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standard success response schema."""

    message: str = Field(..., description="Success message")
