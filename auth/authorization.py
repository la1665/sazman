from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError

from settings import settings
from database.engine import get_db
from auth.auth import oauth2_scheme
from schema.auth import TokenData
from schema.user import UserInDB
from models.user import DBUser, UserType
from crud.user import UserOperation



async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    try:
        if settings.SECRET_KEY and settings.ALGORITHM:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username = payload.get("sub")
            if username is None:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization Error: Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"})
            token_data = TokenData(username=username)
            user_op = UserOperation(db)
            current_user = await user_op.get_user_username(username=token_data.username)
            if current_user is None:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authorization Error: Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"})
            return current_user

    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authorization Error: Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"})


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, {"Permission denied":"Inactive user."}
        )
    return current_user


async def get_viewer_user(current_user: UserInDB = Depends(get_current_active_user)):
    if current_user.user_type not in [UserType.ADMIN, UserType.STAFF, UserType.VIEWER]:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
            {"Permission denied":"Not accessible for this user type."})
    return current_user


async def get_admin_user(current_user: UserInDB = Depends(get_current_active_user)):
    if current_user.user_type is not UserType.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
            {"Permission denied":"Not accessible for this user type."})
    return current_user


async def get_admin_or_staff_user(current_user: DBUser = Depends(get_current_active_user)):
    if current_user.user_type not in [UserType.ADMIN, UserType.STAFF]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"Permission denied":"Not accessible for this user type."}
        )
    return current_user
