from math import ceil

from pydantic import BaseModel, ConfigDict, Field, computed_field


class OutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InputModel(BaseModel):
    pass


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.page_size == 0 or self.total == 0:
            return 0
        return ceil(self.total / self.page_size)
