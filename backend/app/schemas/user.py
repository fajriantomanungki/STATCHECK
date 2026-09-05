import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

UserLevel = Literal["admin", "pjk", "supervisor", "ka_bps", "humas"]


class UserCreate(BaseModel):
    nama: str = Field(min_length=2, max_length=150)
    nik: str = Field(min_length=2, max_length=50)
    user_level: UserLevel
    fungsi: str | None = Field(default=None, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    nama: str = Field(min_length=2, max_length=150)
    nik: str = Field(min_length=2, max_length=50)
    user_level: UserLevel
    fungsi: str | None = Field(default=None, max_length=150)
    is_active: bool = True
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: uuid.UUID
    nama: str
    nik: str
    user_level: str
    fungsi: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
