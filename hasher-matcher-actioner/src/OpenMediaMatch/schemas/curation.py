from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BankConfig(BaseModel):
    """Schema for bank configuration."""

    name: str = Field(..., description="Bank name")
    matching_enabled_ratio: float = Field(
        ..., description="Ratio for enabling matching (0.0-1.0)"
    )


class BankCreateRequest(BaseModel):
    """Request schema for creating a bank."""

    name: str = Field(..., description="Bank name")
    enabled_ratio: Optional[float] = Field(1.0, description="Matching enabled ratio")
    enabled: Optional[bool] = Field(None, description="Whether bank is enabled")


class BankUpdateRequest(BaseModel):
    """Request schema for updating a bank."""

    name: Optional[str] = Field(None, description="New bank name")
    enabled_ratio: Optional[float] = Field(None, description="Matching enabled ratio")
    enabled: Optional[bool] = Field(None, description="Whether bank is enabled")


class BankedContentMetadata(BaseModel):
    """Schema for banked content metadata."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    content_id: Optional[str] = Field(None, description="Content ID")
    content_uri: Optional[str] = Field(None, description="Content URI")
    json_data: Optional[dict[str, Any]] = Field(
        None,
        alias="json",
        serialization_alias="json",
        description="Additional JSON metadata",
    )


class BankContentRequest(BaseModel):
    """Request schema for adding content to a bank."""

    url: Optional[str] = Field(None, description="URL to content")
    metadata: Optional[BankedContentMetadata] = Field(
        None, description="Content metadata"
    )


class BankContentResponse(BaseModel):
    """Response schema for bank content."""

    id: int = Field(..., description="Content ID")
    disable_until_ts: int = Field(..., description="Disable until timestamp")
    collab_metadata: dict[str, list[str]] = Field(
        ..., description="Collaboration metadata"
    )
    original_media_uri: Optional[str] = Field(None, description="Original media URI")
    bank: BankConfig = Field(..., description="Bank configuration")
    signals: Optional[dict[str, str]] = Field(None, description="Signal hashes")


class BankContentUpdateRequest(BaseModel):
    """Request schema for updating bank content."""

    disable_until_ts: Optional[int] = Field(None, description="Disable until timestamp")


class ExchangeCreateRequest(BaseModel):
    """Request schema for creating an exchange."""

    bank: str = Field(..., description="Bank name (must match /^[A-Z0-9_]+$/)")
    api: str = Field(..., description="Exchange API type")
    api_json: dict[str, Any] = Field(
        default_factory=dict, description="Exchange-specific configuration"
    )


class ExchangeConfig(BaseModel):
    """Schema for exchange configuration."""

    model_config = ConfigDict(extra="allow")


class ExchangeUpdateRequest(BaseModel):
    """Request schema for updating an exchange."""

    enabled: Optional[bool] = Field(None, description="Whether exchange is enabled")


class ExchangeApiConfigResponse(BaseModel):
    """Response schema for exchange API configuration."""

    supports_authentification: bool = Field(
        ..., description="Whether API supports authentication"
    )
    has_set_authentification: bool = Field(
        ..., description="Whether credentials are set"
    )


class ExchangeFetchStatus(BaseModel):
    """Schema for exchange fetch status."""

    last_fetch_time: Optional[int] = Field(None, description="Last fetch time")
    checkpoint_time: Optional[int] = Field(None, description="Checkpoint time")
    success: bool = Field(..., description="Whether last fetch succeeded")


class SignalTypeConfig(BaseModel):
    """Schema for signal type configuration."""

    name: str = Field(..., description="Signal type name")
    enabled_ratio: float = Field(..., description="Enabled ratio")


class SignalTypeUpdateRequest(BaseModel):
    """Request schema for updating signal type configuration."""

    enabled_ratio: float = Field(..., description="Enabled ratio")


class ContentTypeConfig(BaseModel):
    """Schema for content type configuration."""

    name: str = Field(..., description="Content type name")
    enabled: bool = Field(..., description="Whether content type is enabled")


class SignalTypeIndexStatus(BaseModel):
    """Schema for signal type index status."""

    db_size: int = Field(..., description="Database size")
    index_size: int = Field(..., description="Index size")
    index_out_of_date: bool = Field(..., description="Whether index is out of date")
    newest_db_item: int = Field(..., description="Newest database item timestamp")
    index_built_to: int = Field(..., description="Index built to timestamp")
