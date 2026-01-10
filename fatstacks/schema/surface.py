from typing import Optional, List

from fatstacks.schema.form import Form
from fatstacks.schema.item import Item
from fatstacks.schema.layout_hints import LayoutHints
from fatstacks.utils.model import Model


class Surface(Model):
    """
    A surface is the top-level container for an application UI screen. An app may have many surfaces to expose different capabilities to the user.

    Surfaces contain items, actions, and forms to allow user interaction. Surfaces also may provide optional layout hints to guide rendering engines on how to display the surface appropriately.
    """

    version: int = 1
    """The version of the surface schema. Currently always 1."""

    id: str
    """A unique identifier for the surface within the application."""
    name: Optional[str]
    """The name of the surface, which will appear in the UI as a title or header."""
    description: Optional[str] = ""
    """A brief description of the surface's purpose or content. This may be shown as a tooltip or subtitle."""

    layoutHints: Optional["LayoutHints"] = None
    """Optional layout hints to guide rendering engines on how to display the surface."""

    items: List["Item"]
    """A list of items that make up the content of the surface."""

    forms: Optional[List["Form"]] = None
    """A list of forms available within the surface for user input and data submission."""
