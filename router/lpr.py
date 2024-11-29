from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.authorization import get_current_active_user, get_viewer_user, get_admin_user, get_admin_or_staff_user
from database.engine import get_db
from schema.user import UserInDB
from schema.lpr import LprCreate, LprUpdate, LprInDB, LprPagination
from crud.lpr import LprOperation
from utils.middlewwares import check_password_changed

# Create an APIRouter for user-related routes
lpr_router = APIRouter(
    prefix="/v1/lprs",
    tags=["lprs"],
)



#lpr endpoints
@lpr_router.post("/", response_model=LprInDB, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_password_changed)])
async def api_create_lpr(
    lpr: LprCreate,
    db: AsyncSession = Depends(get_db),
    current_user:UserInDB=Depends(get_admin_or_staff_user)
):
    lpr_op = LprOperation(db)
    return await lpr_op.create_lpr(lpr)

@lpr_router.get("/", response_model=LprPagination, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_get_all_lprs(
    page: int=1,
    page_size: int=10,
    db: AsyncSession=Depends(get_db),
    current_user:UserInDB=Depends(get_current_active_user)
):
    lpr_op = LprOperation(db)
    return await lpr_op.get_all_objects(page, page_size)

@lpr_router.get("/{lpr_id}", response_model=LprInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_get_lpr(
    lpr_id: int,
    db: AsyncSession=Depends(get_db),
    current_user:UserInDB=Depends(get_current_active_user)
):
    lpr_op = LprOperation(db)
    return await lpr_op.get_one_object_id(lpr_id)

@lpr_router.put("/{lpr_id}", response_model=LprInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_update_lpr(
    lpr_id: int,
    lpr: LprUpdate,
    db:AsyncSession=Depends(get_db),
    current_user:UserInDB=Depends(get_admin_or_staff_user)
):
    lpr_op = LprOperation(db)
    return await lpr_op.update_lpr(lpr_id, lpr)

@lpr_router.delete("/{lpr_id}", response_model=LprInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_delete_lpr(
    lpr_id: int,
    db:AsyncSession=Depends(get_db),
    current_user:UserInDB=Depends(get_admin_or_staff_user)
):
    lpr_op = LprOperation(db)
    return await lpr_op.delete_lpr(lpr_id)

@lpr_router.patch("/{lpr_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_change_activation(
    lpr_id: int,
    db:AsyncSession=Depends(get_db),
    current_user:UserInDB=Depends(get_admin_or_staff_user)
):
    lpr_op = LprOperation(db)
    return await lpr_op.change_activation_status(lpr_id)
