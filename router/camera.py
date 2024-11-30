from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.authorization import get_current_active_user, get_viewer_user, get_admin_user, get_admin_or_staff_user
from database.engine import get_db
from schema.user import UserInDB
from schema.camera import CameraCreate, CameraUpdate, CameraInDB, CameraPagination
from crud.camera import CameraOperation
from utils.middlewwares import check_password_changed


camera_router = APIRouter(
    prefix="/v1/cameras",
    tags=["cameras"],
)


@camera_router.post("/", response_model=CameraInDB, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_password_changed)])
async def api_create_camera(camera: CameraCreate, db: AsyncSession = Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    camera_op = CameraOperation(db)
    return await camera_op.create_camera(camera)

@camera_router.get("/", response_model=CameraPagination, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_get_all_cameras(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    camera_op = CameraOperation(db)
    return await camera_op.get_all_objects(page, page_size)


@camera_router.get("/{camera_id}", response_model=CameraInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_get_gate(camera_id: int, db: AsyncSession = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
    camera_op = CameraOperation(db)
    return await camera_op.get_one_object_id(camera_id)


@camera_router.put("/{camera_id}", response_model=CameraInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_update_camera(camera_id: int, camera: CameraUpdate, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    camera_op = CameraOperation(db)
    return await camera_op.update_camera(camera_id, camera)


@camera_router.delete("/{camera_id}", response_model=CameraInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_delete_camera(camera_id: int, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_or_staff_user)):
    camera_op = CameraOperation(db)
    return await camera_op.delete_object(camera_id)

@camera_router.patch("/{camera_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_password_changed)])
async def api_change_activation(
    camera_id: int,
    db: AsyncSession=Depends(get_db),
    current_user: UserInDB=Depends(get_admin_or_staff_user)
):
    camera_op = CameraOperation(db)
    return await camera_op.change_activation_status(camera_id)
