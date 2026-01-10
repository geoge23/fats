from typing import Any, List, Optional, Type
from pydantic import BaseModel, Field
from enum import Enum


class ActionBehaviorType(str, Enum):
    NAVIGATE = "navigate"
    REQUEST = "request"
    TOAST = "toast"


ActionBehaviorTypes = Type[
    "NavigateActionBehavior | RequestActionBehavior | ToastActionBehavior"
]


class ActionBehavior(BaseModel):
    """Defines the behavior of an action when it is triggered."""

    type: ActionBehaviorType
    """The type of behavior the action performs (e.g., navigate, request, form)."""


class ParamFromData(BaseModel):
    """Indicates that a parameter's value should be taken from the action's data."""

    fromData: str
    """The key in the action's data to use for the parameter's value."""


class NavigateActionBehavior(ActionBehavior):
    """Defines a navigation action behavior that transitions to a specified surface."""

    type = ActionBehaviorType.NAVIGATE

    targetUri: str = Field(pattern=r"^(surface://|https?://).+")
    """The uri to navigate to when the action is triggered. Can use surface:// scheme to refer to internal surfaces."""

    queryParams: Optional[dict[str, str | ParamFromData]] = None
    """Optional query parameters to append to the target URI when navigating. These will be merged with any existing query parameters in the targetUri."""


class RequestActionBehavior(ActionBehavior):
    """Defines a request action behavior that performs an HTTP request to a specified endpoint."""

    type = ActionBehaviorType.REQUEST

    endpoint: str
    """The HTTP endpoint to send the request to when the action is triggered."""

    formToUse: Optional[str] = None
    """The ID of the form whose data should be included in the request, if applicable. This will cause the form to be displayed and its data to be sent along with the request."""

    payload: Optional[Any] = None
    """An optional payload to include in the request body. Will always be merged with data from the item or content override. Will be merged with form data if formToUse is specified."""


class ToastActionBehavior(ActionBehavior):
    """Defines a toast action behavior that displays a brief message to the user."""

    type = ActionBehaviorType.TOAST

    message: str
    """The message to display in the toast notification when the action is triggered."""


class Action(BaseModel):
    """An action represents an operation that can be performed within the application, such as navigating to a different surface, submitting a form, or triggering a specific functionality."""

    id: str
    """A unique identifier for the action."""

    behavior: ActionBehaviorTypes | List[ActionBehaviorTypes]
    """The behavior(s) that defines what happens when the action is triggered. Can be a single behavior or a list of behaviors to perform in sequence."""

    confirm: Optional[bool | str] = False
    """Whether to ask the user for confirmation before executing the action. If a string is provided, it will be used as the confirmation message."""
