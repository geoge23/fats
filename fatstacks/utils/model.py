from pydantic import ConfigDict, BaseModel


class Model(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
