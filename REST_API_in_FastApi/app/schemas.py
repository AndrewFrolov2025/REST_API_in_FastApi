from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field



class AdvertisementBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200, examples=['Телефон Samsung'])

    description: str = Field(min_length=1, max_length=200, examples=['Телефон в рабочем состоянии'])

    price: Decimal = Field(gt=0, max_digits=10_000, decimal_places=2, examples=['33000.00'])

    author: str = Field(min_length=1, max_length=200, examples=['Андрей'])


class AdvertisementCreate(AdvertisementBase):
    pass


class AdvertisementUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)

    description: str | None = Field(default=None, min_length=1, max_length=200)

    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)

    author: str | None = Field(default=None, min_length=1, max_length=200)


class AdvertisementRead(AdvertisementBase):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: int
    create_at: datetime