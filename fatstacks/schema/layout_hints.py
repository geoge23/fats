from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class LayoutStyle(str, Enum):
    LIST = "list"


class LayoutHints(BaseModel):
    """
    Layout hints provide optional guidance on how to render a surface's contents. They can suggest layout styles, themes, and other visual preferences to help rendering engines display the surface appropriately.

    Layout hints are not strict requirements but rather suggestions that rendering engines may choose to follow based on their capabilities and context.
    """

    color: Optional[str] = Field(pattern=r"^\#[0-9a-fA-F]{6}$")
    """A preferred color scheme for the surface, specified as a hex code (e.g., "#RRGGBB")"""

    layoutStyle: Optional[LayoutStyle] = None
    """A suggested layout style for arranging items within the surface (e.g., 'list')."""
