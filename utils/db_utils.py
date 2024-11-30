from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserType
from settings import settings
from crud.user import UserOperation
from crud.building import BuildingOperation
from crud.gate import GateOperation
from crud.camera import CameraOperation
from crud.lpr import LprOperation
from schema.user import UserCreate
from schema.building import BuildingCreate
from schema.gate import GateCreate
from schema.camera import CameraCreate
from schema.lpr import LprCreate
from tcp.tcp_manager import add_connection


default_buildings = [
    {
      "name": "مرکزی",
      "latitude": "98.0.0",
      "longitude": "98.0.0",
      "description": "شعبه مرکزی"
    },
    {
      "name": "آمل",
      "latitude": "98.0.1",
      "longitude": "98.0.1",
      "description": "شعبه آمل"
    }
]

default_gates = [
    {
      "name": "گیت اصلی ساختمان مرکزی",
      "description": "گیت اصلی شعبه مرکزی تهران",
      "gate_type": 2,
      "building_id": 1
    },
    {
      "name": "گیت ورودی",
      "description": "گیت ورودی شعبه مرکزی",
      "gate_type": 0,
      "building_id": 1
    },
    {
      "name": "گیت خروجی",
      "description": "گیت خروجی سازمان مرکزی",
      "gate_type": 1,
      "building_id": 1
    },
    {
      "name": "گیت ورودی/خروجی شعبه",
      "description": "گیت اصلی شعبه آمل",
      "gate_type": 2,
      "building_id": 2
    }
]

default_lprs = [
    {
      "name": "ماژول پلاک خوان۱",
      "description": "پلاک خوان دوربین گیت۱ برای ورودی/خروجی",
      "ip": "185.81.99.23",
      "port": 45,
      "latitude": "98.0.0",
      "longitude": "98.0.0",
    },
    {
      "name": "ماژول پلاک خوان۲",
      "description": "پلاک خوان دوربین گیت۱ برای ورودی/خروجی",
      "ip": "185.81.99.23",
      "port": 46,
      "latitude": "98.0.0",
      "longitude": "98.0.0",
    },
    {
      "name": "ماژول پلاک خوان۳",
      "description": "پلاک خوان دوربین گیت۱ برای ورودی",
      "ip": "185.81.99.23",
      "port": 47,
      "latitude": "98.0.0",
      "longitude": "98.0.0",
    },
    {
      "name": "ماژول پلاک خوان۴",
      "description": "پلاک خوان دوربین گیت۱ برای خروجی",
      "ip": "185.81.99.23",
      "port": 48,
      "latitude": "98.0.0",
      "longitude": "98.0.0",
    },
    {
      "name": "ماژول پلاک خوان۵",
      "description": "پلاک خوان دوربین گیت۲ برای ورودی/خروجی",
      "ip": "185.81.99.23",
      "port": 49,
      "latitude": "98.0.0",
      "longitude": "98.0.0",
    }
]


default_cameras = [
    {
      "name": "دوربین ۱",
      "latitude": "1.0.1",
      "longitude": "1.0.1",
      "description": "دوربین اصلی گیت",
      "gate_id": 1,
      "lpr_ids": [1],
    },
    {
      "name": "دوربین دوم",
      "latitude": "2.0.1",
      "longitude": "2.0.1",
      "description": "دوربین گیت ورود",
      "gate_id": 2,
      "lpr_ids": [1,2],
    },
    {
      "name": "دوربین سوم",
      "latitude": "3.0.1",
      "longitude": "3.0.1",
      "description": "دوربین گیت خروج",
      "gate_id": 3,
      "lpr_ids": [3,5],
    },
    {
      "name": "دوربین گیت اصلی",
      "latitude": "4.0.1",
      "longitude": "4.0.1",
      "description": "دوربین اصلی(ورود/خروج)",
      "gate_id": 4,
      "lpr_ids": [],
    },
]



async def create_default_admin(db: AsyncSession):
    if settings.ADMIN_USERNAME:
        user_op = UserOperation(db)
        db_admin = await user_op.get_user_username(settings.ADMIN_USERNAME)
        if db_admin:
            print("Admin user already exists.")
            return

        admin = UserCreate(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            user_type=UserType.ADMIN
        )
        admin = await user_op.create_user(admin)
        print("Admin user created.")

async def initialize_defaults(db: AsyncSession):
    building_op = BuildingOperation(db)
    for building in default_buildings:
        db_building = await building_op.get_one_object_name(building.get("name"))
        if db_building:
            print("building object already exists.")
            return
        building_obj = BuildingCreate(
            name=building["name"],
            description=building["description"],
            latitude=building["latitude"],
            longitude=building["longitude"],
        )
        new_building = await building_op.create_building(building_obj)
        print(f"Created building with ID: {new_building.id}")
    print("default buildings created!!!")

    gate_op = GateOperation(db)
    for gate in default_gates:
        db_gate = await gate_op.get_one_object_name(gate.get("name"))
        if db_gate:
            print("gate object already exists.")
            return
        gate_obj = GateCreate(
            name=gate["name"],
            description=gate["description"],
            gate_type=gate["gate_type"],
            building_id=gate["building_id"],
        )
        new_gate = await gate_op.create_gate(gate_obj)
        print(f"Created gate with ID: {new_gate.id}")
    print("default gates created!!!")

    lpr_op = LprOperation(db)
    for lpr in default_lprs:
        db_lpr = await lpr_op.get_one_object_name(lpr.get("name"))
        if db_lpr:
            print("lpr object already exists.")
            print("connecting to twisted ...")
            await add_connection(db_lpr.id, db_lpr.ip, db_lpr.port, db_lpr.auth_token)
            return
        lpr_obj = LprCreate(
            name=lpr["name"],
            description=lpr["description"],
            latitude=lpr["latitude"],
            longitude=lpr["longitude"],
            ip=lpr["ip"],
            port=lpr["port"],
        )
        new_lpr = await lpr_op.create_lpr(lpr_obj)
        print(f"Created lpr with ID: {new_lpr.id}")
    print("default lprs created!!!")

    camera_op = CameraOperation(db)
    for camera in default_cameras:
        db_camera = await camera_op.get_one_object_name(camera.get("name"))
        if db_camera:
            print("camera object already exists.")
            return
        camera_obj = CameraCreate(
            name=camera["name"],
            description=camera["description"],
            latitude=camera["latitude"],
            longitude=camera["longitude"],
            gate_id=camera["gate_id"],
            lpr_ids=camera["lpr_ids"],
        )
        new_camera = await camera_op.create_camera(camera_obj)
        print(f"Created camera with ID: {new_camera.id}")
    print("default cameras created!!!")
