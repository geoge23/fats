from typing import Optional, Type
from enum import Enum

from fatstacks.utils.model import Model


class InputFieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"


InputFieldTypes = Type["TextInputField | NumberInputField | SelectInputField"]


class InputField(Model):
    type: InputFieldType
    """The type of input field (e.g., text, number, select)."""
    name: str
    """The name of the input field, which will be used as the key when submitting data."""


class TextInputField(InputField):
    type: InputFieldType = InputFieldType.TEXT
    """A text input field."""
    placeholder: Optional[str] = None
    """An optional placeholder text for the input field."""


class NumberInputField(InputField):
    type: InputFieldType = InputFieldType.NUMBER
    """A number input field."""


class SelectInputField(InputField):
    type: InputFieldType = InputFieldType.SELECT
    """A select input field."""
    options: list[str]
    """A list of options available for selection."""


class Form(Model):
    """
    A form represents a collection of input fields and actions that allow users to submit data or perform operations within a surface.
    """

    id: str
    """A unique identifier for the form within the surface."""
    name: Optional[str]
    """The name of the form, which may be displayed as a title or header."""
    description: Optional[str] = ""
    """A brief description of the form's purpose or instructions for the user."""

    inputFields: list[InputFieldTypes]
