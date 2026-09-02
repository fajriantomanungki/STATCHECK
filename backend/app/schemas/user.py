import uuid

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    id: uuid.UUID
    nama: str
    nik: str
    user_level: str
    fungsi: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
