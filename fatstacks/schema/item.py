from typing import Dict, List, Optional, Type
from enum import Enum

from fatstacks.utils.model import Model


class DisplayStrategy(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    ACTION = "action"
    AUTO = "auto"


ContentPrimitive = str | int | float | bool
ContentTypes = Type["ContentAuto | ContentText | ContentImage | ContentAction"]


class Content(Model):
    type: DisplayStrategy = DisplayStrategy.AUTO
    """The display strategy for the content, indicating how it should be rendered (e.g., 'text', 'image', etc.). Will be auto-detected if not provided."""
    pass


class ContentAuto(Content):
    type: DisplayStrategy = DisplayStrategy.AUTO
    """Content that will be auto-detected and displayed accordingly."""
    content: ContentPrimitive
    """The primitive content to be auto-displayed."""


class ContentTextSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ContentText(Content):
    type: DisplayStrategy = DisplayStrategy.TEXT
    text: str
    size: Optional[ContentTextSize] = None
    """The text content to be displayed."""


class ContentImage(Content):
    type: DisplayStrategy = DisplayStrategy.IMAGE
    url: str
    """The URL of the image to be displayed."""


class ContentAction(Content):
    type: DisplayStrategy = DisplayStrategy.ACTION
    action: str
    """The identifier of the action to be triggered."""
    data: Optional[Dict[str, ContentPrimitive]] = None
    """Allows overriding the Item data when this action is triggered, instead passing the data defined here."""


class Item(Model):
    """
    An item represents a discrete piece of content within a surface.
    """

    id: str
    """A unique identifier for the item within the surface."""

    content: (
        Dict[str, "ContentTypes | ContentPrimitive"]
        | List["ContentTypes | ContentPrimitive"]
        | ContentTypes
        | ContentPrimitive
    )
    """The content of the item, which can be a dictionary, list, or single content object. The content structure is flexible to accommodate various types of data, chiefly auto-displaying JSON data."""

    data: Optional[Dict[str, ContentPrimitive]]
    """Data to be passed to actions associated with this item."""

    actions: Optional[List[str]] = []
    """A list of action identifiers that can be triggered from this item."""
