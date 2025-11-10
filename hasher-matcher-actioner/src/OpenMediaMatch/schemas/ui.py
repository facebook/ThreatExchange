from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateBankFormRequest(BaseModel):
    """Request schema for creating bank via UI form."""

    bank_name: str = Field(..., description="Bank name")


class QueryFormRequest(BaseModel):
    """Request schema for query form submission."""

    bypass_enabled_ratio: bool = Field(
        True, description="Whether to bypass enabled ratio"
    )


class QueryUrlRequest(BaseModel):
    """Request schema for URL query."""

    url: str = Field(..., description="URL to query")
    content_type: str = Field(..., description="Content type")
    bypass_enabled_ratio: bool = Field(
        True, description="Whether to bypass enabled ratio"
    )


class QueryHashRequest(BaseModel):
    """Request schema for hash query."""

    signal_type: str = Field(..., description="Signal type")
    signal_value: str = Field(..., description="Signal value")
    bypass_enabled_ratio: bool = Field(
        True, description="Whether to bypass enabled ratio"
    )


class QueryResponse(BaseModel):
    """Response schema for query operations."""

    hashes: dict[str, str] = Field(..., description="Generated hashes")
    banks: list[str] = Field(..., description="List of banks")
    matches: list[dict[str, Any]] = Field(..., description="List of matches")


class BankFindContentRequest(BaseModel):
    """Request schema for finding content in bank."""

    url: Optional[str] = Field(None, description="URL to search")
    content_type: Optional[str] = Field(None, description="Content type for URL")
    signal_type: Optional[str] = Field(None, description="Signal type for hash search")
    signal_value: Optional[str] = Field(
        None, description="Signal value for hash search"
    )


class BankFindContentResponse(BaseModel):
    """Response schema for finding content in bank."""

    content_ids: list[int] = Field(..., description="List of content IDs")
    matches: list[dict[str, Any]] = Field(..., description="List of matches")
    bank_name: str = Field(..., description="Bank name")
