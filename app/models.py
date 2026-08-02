"""Pydantic request/response models for the URL-shortener API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LinkCreate(BaseModel):
    """Payload for creating a short link."""

    url: str = Field(..., description="The destination URL to shorten.")


class LinkOut(BaseModel):
    """A created short link."""

    code: str = Field(..., description="The short code identifying the link.")
    url: str = Field(..., description="The destination URL.")
