from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# from models.user import UserType
from schema.building import BuildingInDB
from schema.gate import GateInDB
from schema.pagination import Pagination
from schema.user import UserInDB


class TrafficBase(BaseModel):
    plate_number: str
    camera_id: int
    ocr_accuracy: str
    vision_speed: str
    timestamp: datetime


class TrafficCreate(TrafficBase):
    pass


class TrafficUpdate(BaseModel):
    pass


class TrafficInDB(TrafficBase):
    id: int
    owner_username: Optional[str] = None
    owner_first_name: Optional[str] = None
    owner_last_name: Optional[str] = None
    building_name: Optional[str] = None
    gate_name: Optional[str] = None

    class Config:
        from_attributes = True


TrafficPagination = Pagination[TrafficInDB]
