from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Generic, List, TypeVar, TYPE_CHECKING

from schema.pagination import Pagination


class LprSummary(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CameraBase(BaseModel):
    name: str
    latitude: str
    longitude: str
    description: str


class CameraCreate(CameraBase):
    gate_id: int
    lpr_ids: Optional[List[int]] = []


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    description: Optional[str] = None
    gate_id: Optional[int] = None
    lpr_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class CameraInDB(CameraBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    gate_id: int
    lprs: List[LprSummary] = []

    class Config:
        from_attributes = True


CameraPagination = Pagination[CameraInDB]
