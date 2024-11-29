from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CrudOperation
from models.building import DBBuilding
from schema.building import BuildingUpdate, BuildingCreate




class BuildingOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession, de_table=DBBuilding) -> None:
        super().__init__(db_session, DBBuilding)

    async def create_building(self, building:BuildingCreate):
        db_building = await self.get_one_object_name(building.name)
        if db_building:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "building already exists.")

        try:
            new_building = DBBuilding(
                name=building.name,
                latitude=building.latitude,
                longitude=building.longitude,
                description=building.description
            )
            self.db_session.add(new_building)
            await self.db_session.commit()
            await self.db_session.refresh(new_building)
            return new_building
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Failed to create building.")


    async def update_building(self, building_id: int, building_update: BuildingUpdate):
        db_building = await self.get_one_object_id(building_id)
        try:
            for key, value in building_update.dict(exclude_unset=True).items():
                setattr(db_building, key, value)
            self.db_session.add(db_building)
            await self.db_session.commit()
            await self.db_session.refresh(db_building)
            return db_building
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{error}: Failed to update building."
            )
