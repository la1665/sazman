from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CrudOperation
from crud.building import BuildingOperation
from models.gate import DBGate
from schema.gate import GateUpdate, GateCreate




class GateOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession, de_table=DBGate) -> None:
        super().__init__(db_session, DBGate)

    async def create_gate(self, gate:GateCreate):
        db_gate = await self.get_one_object_name(gate.name)
        if db_gate:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "gate already exists.")
        db_building = await BuildingOperation(self.db_session).get_one_object_id(gate.building_id)
        try:
            new_gate = DBGate(
                name=gate.name,
                gate_type=gate.gate_type,
                description=gate.description,
                building_id=db_building.id
            )
            self.db_session.add(new_gate)
            await self.db_session.commit()
            await self.db_session.refresh(new_gate)
            return new_gate
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Failed to create gate.")


    async def update_gate(self, gate_id: int, gate_update: GateUpdate):
        db_gate = await self.get_one_object_id(gate_id)
        try:
            update_data = gate_update.dict(exclude_unset=True)
            if "building_id" in update_data:
                building_id = update_data["building_id"]
                await BuildingOperation(self.db_session).get_one_object_id(building_id)
                db_gate.building_id = building_id

            for key, value in update_data.items():
                if key != "building_id":
                    setattr(db_gate, key, value)
            self.db_session.add(db_gate)
            await self.db_session.commit()
            await self.db_session.refresh(db_gate)
            return db_gate
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{error}: Failed to update gate."
            )
