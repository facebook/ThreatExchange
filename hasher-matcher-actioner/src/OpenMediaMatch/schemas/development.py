from pydantic import BaseModel, Field


class SeedSampleResponse(BaseModel):
    """Response schema for seeding sample data."""

    message: str = Field(
        "Sample data seeded successfully", description="Success message"
    )


class SetupTxExampleRequest(BaseModel):
    """Request schema for setting up ThreatExchange example."""

    pass
