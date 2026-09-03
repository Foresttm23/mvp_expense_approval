from pydantic import BaseModel, ConfigDict


class OutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InputModel(BaseModel):
    pass
