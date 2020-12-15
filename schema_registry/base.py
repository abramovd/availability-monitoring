import abc

from pydantic import BaseModel


class BaseSchema(abc.ABC):
    pass


class BasePydanticSchema(BaseSchema, BaseModel):
    pass
