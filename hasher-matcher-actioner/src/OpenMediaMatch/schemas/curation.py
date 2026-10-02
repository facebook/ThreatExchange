# Copyright (c) Meta Platforms, Inc. and affiliates.

from typing import Any, Literal, Optional

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
    """
    Schema for banked content metadata.

    Combines user-supplied metadata (content_id, content_uri, json) with
    collaboration/exchange provenance data (collab).
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    content_id: Optional[str] = Field(None, description="Content ID")
    content_uri: Optional[str] = Field(None, description="Content URI")
    json_data: Optional[dict[str, Any]] = Field(
        None,
        alias="json",
        serialization_alias="json",
        description="Additional JSON metadata",
    )
    collab: Optional[dict[str, list[str]]] = Field(
        None,
        description="Collaboration/exchange provenance: maps exchange name to fetch keys",
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
    original_media_uri: Optional[str] = Field(None, description="Original media URI")
    bank: BankConfig = Field(..., description="Bank configuration")
    signals: Optional[dict[str, str]] = Field(None, description="Signal hashes")
    metadata: Optional[BankedContentMetadata] = Field(
        None,
        description="Content metadata including user-supplied data and collaboration provenance",
    )
    note: Optional[str] = Field(None, description="User-supplied note (max 255 chars)")


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
    credential_json: Optional[dict[str, Any]] = Field(
        None,
        description=(
            "Optional credentials used only by this exchange, matching the "
            "API's credentials_schema (see /c/exchanges/api/<api_name>/schema). "
            "Rejected with 400 if the API does not support credentials."
        ),
    )


class ExchangeCredentialStatus(BaseModel):
    """Which credentials an exchange will use. Never includes secret values."""

    supports_auth: bool = Field(
        ..., description="Whether the exchange's API uses credentials"
    )
    has_credentials: bool = Field(
        ..., description="Whether any credentials are available for this exchange"
    )
    source: Optional[Literal["exchange", "api", "environment", "file"]] = Field(
        None,
        description=(
            "Where the credentials come from, in resolution order: 'exchange' "
            "(set on this exchange), 'api' (API-level default from "
            "/c/exchanges/api/<api_name>), 'environment' or 'file' (deployment "
            "fallbacks). null if none are available."
        ),
    )


class ExchangeCredentialsUpdateRequest(BaseModel):
    """Request schema for setting credentials on a single exchange."""

    credential_json: Optional[dict[str, Any]] = Field(
        ...,
        description=(
            "Credentials matching the API's credentials_schema. "
            "null or {} clears this exchange's credentials, so it falls back "
            "to API-level or environment credentials."
        ),
    )


class ExchangeConfig(BaseModel):
    """Schema for exchange configuration."""

    model_config = ConfigDict(extra="allow")

    credential_status: Optional[ExchangeCredentialStatus] = Field(
        None, description="Credential status for this exchange (no secret values)"
    )


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
