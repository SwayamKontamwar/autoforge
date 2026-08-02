"""Pydantic request/response models for the URL-shortener API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LinkCreate(BaseModel):
    """Payload for creating a short link."""

    url: str = Field(..., description="The destination URL to shorten.")
    alias: str | None = Field(
        None,
        description=(
            "Optional custom alias for the short link. Must be URL‑safe, 3‑32 characters long."
        ),
    )


class LinkOut(BaseModel):
    """A created short link."""

    code: str = Field(..., description="The short code identifying the link.")
    url: str = Field(..., description="The destination URL.")


class LinkInfoOut(BaseModel):
    """Detailed information about a short link."""

    code: str = Field(..., description="The short code identifying the link.")
    url: str = Field(..., description="The destination URL.")
    created_at: datetime = Field(..., description="Timestamp when the link was created.")
    hits: int = Field(..., description="Number of times the link has been accessed via redirect.")
