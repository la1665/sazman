import math
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CrudOperation
from crud.building import BuildingOperation
from crud.gate import GateOperation
from crud.camera import CameraOperation
from crud.user import UserOperation
from crud.vehicle import VehicleOperation
from models.traffic import DBTraffic
from schema.user import UserInDB
from schema.building import BuildingInDB
from schema.gate import GateInDB
from schema.traffic import TrafficCreate, TrafficInDB


class TrafficOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__(db_session, DBTraffic)

    async def create_traffic(self, traffic: TrafficCreate):
        db_vehicle = await VehicleOperation(self.db_session).get_one_vehcile_plate(traffic.plate_number)
        db_user = await UserOperation(self.db_session).get_one_object_id(db_vehicle.owner_id) if db_vehicle and db_vehicle.owner_id else None
        db_camera = await CameraOperation(self.db_session).get_one_object_id(traffic.camera_id)
        db_gate = await GateOperation(self.db_session).get_one_object_id(db_camera.gate_id)
        db_building = await BuildingOperation(self.db_session).get_one_object_id(db_gate.building_id)

        try:
            naive_timestamp = traffic.timestamp.replace(tzinfo=None)
            new_traffic = self.db_table(
                plate_number = traffic.plate_number,
                ocr_accuracy = traffic.ocr_accuracy,
                vision_speed = traffic.vision_speed,
                timestamp = naive_timestamp,
                camera_id = db_camera.id,
            )
            self.db_session.add(new_traffic)
            await self.db_session.commit()
            await self.db_session.refresh(new_traffic)
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Failed to create traffic.")


        return TrafficInDB(
            **new_traffic.__dict__,
            owner_username=db_user.username if db_user else None,
            owner_first_name=db_user.first_name if db_user else None,
            owner_last_name=db_user.last_name if db_user else None,
            building_name=db_building.name if db_building else None,
            gate_name=db_gate.name if db_gate else None,
        )


    async def get_all_traffics(self, page: int=1, page_size: int=10):
        total_query = await self.db_session.execute(select(func.count(self.db_table.id)))
        total_records = total_query.scalar_one()

        # Calculate total number of pages
        total_pages = math.ceil(total_records / page_size) if page_size else 1

        # Calculate offset
        offset = (page - 1) * page_size

        # Fetch the records
        query = await self.db_session.execute(
            select(self.db_table).offset(offset).limit(page_size)
        )
        objects = query.unique().scalars().all()
        results = []
        for object in objects:
            db_vehicle = await VehicleOperation(self.db_session).get_one_vehcile_plate(object.plate_number)
            db_user = await UserOperation(self.db_session).get_one_object_id(db_vehicle.owner_id) if db_vehicle and db_vehicle.owner_id else None
            db_camera = await CameraOperation(self.db_session).get_one_object_id(object.camera_id)
            db_gate = await GateOperation(self.db_session).get_one_object_id(db_camera.gate_id)
            db_building = await BuildingOperation(self.db_session).get_one_object_id(db_gate.building_id)
            result = TrafficInDB(
                **object.__dict__,
                owner_username=db_user.username if db_user else None,
                owner_first_name=db_user.first_name if db_user else None,
                owner_last_name=db_user.last_name if db_user else None,
                building_name=db_building.name if db_building else None,
                gate_name=db_gate.name if db_gate else None,
            )
            results.append(result)
        return {
            "items": results,
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
        }
