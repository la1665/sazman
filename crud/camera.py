from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from crud.base import CrudOperation
from crud.gate import GateOperation
from models.camera import DBCamera
from models.lpr import DBLpr
from schema.camera import CameraUpdate, CameraCreate




class CameraOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession, de_table=DBCamera) -> None:
        super().__init__(db_session, DBCamera)

    async def create_camera(self, camera: CameraCreate):
        db_camera = await self.get_one_object_name(camera.name)
        if db_camera:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "camera already exists.")
        db_gate = await GateOperation(self.db_session).get_one_object_id(camera.gate_id)
        try:
            new_camera = DBCamera(
                name=camera.name,
                latitude=camera.latitude,
                longitude=camera.longitude,
                description=camera.description,
                gate_id=db_gate.id
            )

            camera_data = camera.dict()
            lpr_ids = camera_data.pop("lpr_ids", [])
            if lpr_ids:
                lprs = await self.db_session.execute(select(DBLpr).filter(DBLpr.id.in_(lpr_ids)))
                new_camera.lprs = lprs.unique().scalars().all()

            self.db_session.add(new_camera)
            await self.db_session.commit()
            await self.db_session.refresh(new_camera)
            return new_camera
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Failed to create camera.")


    async def update_camera(self, camera_id: int, camera_update: CameraUpdate):
        db_camera = await self.get_one_object_id(camera_id)
        try:
            update_data = camera_update.dict(exclude_unset=True)
            if "gate_id" in update_data:
                gate_id = update_data.pop("gate_id", None)
                await GateOperation(self.db_session).get_one_object_id(gate_id)
                db_camera.gate_id = gate_id

            lpr_ids = update_data.pop("lpr_ids", None)

            for key, value in update_data.items():
                # if key != "gate_id":
                setattr(db_camera, key, value)

            if lpr_ids is not None:
                if lpr_ids:
                    lprs = await self.db_session.execute(select(DBLpr).filter(DBLpr.id.in_(lpr_ids)))
                    db_camera.lprs = lprs.unique().scalars().all()
                else:
                    db_camera.lprs = []

            self.db_session.add(db_camera)
            await self.db_session.commit()
            await self.db_session.refresh(db_camera)
            return db_camera
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{error}: Failed to update camera."
            )
