from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class MatchWithDistance(BaseModel):
    """Schema for a match result with distance."""

    bank_content_id: int = Field(..., description="ID of the matched content")
    distance: str = Field(..., description="Distance/similarity score")


class RawLookupRequest(BaseModel):
    """Request schema for raw hash lookup."""

    signal: str = Field(..., description="The hash/signal to look up")
    signal_type: str = Field(..., description="Type of signal (pdq, video_md5, etc.)")
    banks: Optional[str] = Field(
        None, description="Comma-separated list of banks to search"
    )
    include_distance: bool = Field(
        False, description="Whether to include distance in results"
    )


class RawLookupResponse(BaseModel):
    """Response schema for raw hash lookup."""

    matches: list[Union[int, MatchWithDistance]] = Field(
        ..., description="List of matches"
    )


class LookupRequest(BaseModel):
    """Request schema for content lookup."""

    url: Optional[str] = Field(None, description="URL to hash and lookup")
    content_type: Optional[str] = Field(None, description="Content type for URL")
    types: Optional[str] = Field(
        None,
        description="Comma-separated list of signal types to hash when using a URL",
    )
    signal: Optional[str] = Field(None, description="Hash/signal to lookup")
    signal_type: Optional[str] = Field(None, description="Type of signal")
    banks: Optional[str] = Field(
        None, description="Comma-separated list of banks to search"
    )
    seed: Optional[str] = Field(None, description="Seed for consistent coinflip")
    bypass_coinflip: bool = Field(
        False, description="Whether to bypass enabled ratio check"
    )


class LookupResponse(BaseModel):
    """Response schema for content lookup."""

    model_config = ConfigDict(extra="allow")


class CompareRequest(BaseModel):
    """Request schema for hash comparison."""

    model_config = ConfigDict(extra="allow")


class CompareResponse(BaseModel):
    """Response schema for hash comparison."""

    model_config = ConfigDict(extra="allow")


class IndexStatusResponse(BaseModel):
    """Response schema for index status."""

    model_config = ConfigDict(extra="allow")
