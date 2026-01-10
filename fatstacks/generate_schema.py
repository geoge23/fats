from typing import List, Type
from fatstacks.schema.action import Action
from fatstacks.schema.app import App
from fatstacks.schema.form import Form
from fatstacks.schema.item import Item
from fatstacks.schema.layout_hints import LayoutHints
from fatstacks.schema.surface import Surface
import json

from fatstacks.utils.model import Model


schemas_to_generate: List[Type[Model]] = [
    Action,
    App,
    Form,
    Item,
    LayoutHints,
    Surface,
]

for schema in schemas_to_generate:
    schema_data = schema.model_json_schema()
    schema_filename = f"{schema.__name__.lower()}_schema.json"
    with open(schema_filename, "w") as f:
        f.write(json.dumps(schema_data, indent=4))
    print(f"Generated schema for {schema.__name__} in {schema_filename}")
