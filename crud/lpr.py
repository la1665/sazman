from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from crud.base import CrudOperation
from models.lpr import DBLpr
from schema.lpr import LprUpdate, LprCreate
from tcp.tcp_manager import add_connection, update_connection, remove_connection


class LprOperation(CrudOperation):
    def __init__(self, db_session: AsyncSession, de_table=DBLpr) -> None:
        super().__init__(db_session, DBLpr)

    async def create_lpr(self, lpr:LprCreate):
        db_lpr = await self.get_one_object_name(lpr.name)
        if db_lpr:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "lpr already exists.")

        try:
            new_lpr = self.db_table(
                name=lpr.name,
                ip=lpr.ip,
                port=lpr.port,
                auth_token=settings.LPR_AUTH_TOKEN,
                latitude=lpr.latitude,
                longitude=lpr.longitude,
                description=lpr.description,
            )
            self.db_session.add(new_lpr)
            await self.db_session.commit()
            await self.db_session.refresh(new_lpr)

            # Add connection to Twisted
            await add_connection(new_lpr.id, new_lpr.ip, new_lpr.port, new_lpr.auth_token)

            return new_lpr
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Failed to create lpr.")


    async def update_lpr(self, lpr_id: int, lpr_update: LprUpdate):
        db_lpr = await self.get_one_object_id(lpr_id)
        try:
            for key, value in lpr_update.dict(exclude_unset=True).items():
                setattr(db_lpr, key, value)
            self.db_session.add(db_lpr)
            await self.db_session.commit()
            await self.db_session.refresh(db_lpr)

            # Update connection in Twisted
            await update_connection(db_lpr.id, db_lpr.ip, db_lpr.port, db_lpr.auth_token)

            return db_lpr
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{error}: Failed to update lpr."
            )

    async def delete_lpr(self, lpr_id: int):
        db_lpr = await self.get_one_object_id(lpr_id)
        try:
            await self.db_session.delete(db_lpr)
            await self.db_session.commit()

            # Remove connection from Twisted
            remove_connection(lpr_id)

            return {"message": f"LPR {lpr_id} deleted successfully"}
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Failed to delete LPR.")
