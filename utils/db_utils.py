from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserType
from models.camera_setting import SettingType
from models.lpr_setting import LprSettingType
from settings import settings
from crud.user import UserOperation
from crud.building import BuildingOperation
from crud.gate import GateOperation
from crud.camera_setting import CameraSettingOperation
from crud.lpr_setting import LprSettingOperation
from crud.lpr import LprOperation
from crud.camera import CameraOperation
from schema.user import UserCreate
from schema.building import BuildingCreate
from schema.gate import GateCreate
from schema.camera_setting import CameraSettingCreate
from schema.lpr_setting import LprSettingCreate
from schema.lpr import LprCreate
from schema.camera import CameraCreate
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

default_camera_settings = [
    {"name": "ViewPointX", "description": "مختصات X نقطه دید", "value": "0", "setting_type": SettingType.INT},
    {"name": "ViewPointY", "description": "مختصات Y نقطه دید", "value": "0", "setting_type": SettingType.INT},
    {"name": "ViewPointWidth", "description": "عرض نقطه دید", "value": "1920", "setting_type": SettingType.INT},
    {"name": "ViewPointHeight", "description": "ارتفاع نقطه دید", "value": "1080", "setting_type": SettingType.INT},
    {"name": "MaxDeviation", "description": "حساسیت تشخیص شیء - انحراف حداکثر", "value": "100", "setting_type": SettingType.INT},
    {"name": "MinDeviation", "description": "حساسیت تشخیص شیء - انحراف حداقل", "value": "5", "setting_type": SettingType.INT},
    {"name": "ObjectSize", "description": "حداقل اندازه شیء برای تشخیص", "value": "250", "setting_type": SettingType.INT},
    {"name": "BufferSize", "description": "اندازه بافر", "value": "10", "setting_type": SettingType.INT},
    {"name": "CameraDelayTime", "description": "زمان تأخیر دوربین", "value": "200", "setting_type": SettingType.INT},
    {"name": "CameraAddress", "description": "آدرس RTSP دوربین", "value": "D:\\programs\\test_video\\+-1_20230920-112542_1_189.avi", "setting_type": SettingType.STRING},
    {"name": "live_scale", "description": "ضریب مقیاس زنده", "value": "1", "setting_type": SettingType.INT},
    {"name": "recive_plate_status", "description": "دریافت وضعیت پلاک", "value": "0", "setting_type": SettingType.INT},
    {"name": "relay_ip", "description": "آدرس IP رله", "value": "192.168.1.91", "setting_type": SettingType.STRING},
    {"name": "relay_port", "description": "پورت رله", "value": "2000", "setting_type": SettingType.INT},
    {"name": "type_of_link", "description": "نوع پیوند", "value": "rtsp", "setting_type": SettingType.STRING},
]


default_lpr_settings = [
    {"name": "deep_plate_width_1", "description": "عرض تشخیص پلاک اول", "value": "640", "setting_type": LprSettingType.INT},
    {"name": "deep_plate_width_2", "description": "عرض تشخیص پلاک دوم", "value": "640", "setting_type": LprSettingType.INT},
    {"name": "deep_plate_height", "description": "ارتفاع تشخیص پلاک", "value": "480", "setting_type": LprSettingType.INT},
    {"name": "deep_width", "description": "عرض تصویر تشخیص پلاک", "value": "1280", "setting_type": LprSettingType.INT},
    {"name": "deep_height", "description": "ارتفاع تصویر تشخیص پلاک", "value": "736", "setting_type": LprSettingType.INT},
    {"name": "deep_detect_prob", "description": "احتمال تشخیص پلاک", "value": "0.55", "setting_type": LprSettingType.FLOAT},
    {"name": "max_IOU", "description": "بیشترین ترکیب تلاقی", "value": "0.95", "setting_type": LprSettingType.FLOAT},
    {"name": "min_IOU", "description": "کمترین ترکیب تلاقی", "value": "0.85", "setting_type": LprSettingType.FLOAT},
    {"name": "nation_alpr", "description": "تشخیص پلاک ملی", "value": "0", "setting_type": LprSettingType.INT},
    {"name": "ocr_file", "description": "فایل OCR", "value": "ocr_int_model_1.xml", "setting_type": LprSettingType.STRING},
    {"name": "plate_detection_file", "description": "فایل تشخیص پلاک", "value": "plate_model.xml", "setting_type": LprSettingType.STRING},
    {"name": "car_file", "description": "فایل تشخیص خودرو", "value": "car_model.xml", "setting_type": LprSettingType.STRING},
    {"name": "ocr_prob", "description": "احتمال انتخاب OCR", "value": "0.65", "setting_type": LprSettingType.FLOAT},
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
      "gate_id": 1,
      "lpr_ids": [1,2],
    },
    {
      "name": "دوربین سوم",
      "latitude": "3.0.1",
      "longitude": "3.0.1",
      "description": "دوربین گیت خروج",
      "gate_id": 2,
      "lpr_ids": [3],
    },
    {
      "name": "دوربین گیت اصلی",
      "latitude": "4.0.1",
      "longitude": "4.0.1",
      "description": "دوربین اصلی(ورود/خروج)",
      "gate_id": 4,
      "lpr_ids": [2,3,4],
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
        if db_building is None:

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
        if db_gate is None:
            gate_obj = GateCreate(
                name=gate["name"],
                description=gate["description"],
                gate_type=gate["gate_type"],
                building_id=gate["building_id"],
            )
            new_gate = await gate_op.create_gate(gate_obj)
            print(f"Created gate with ID: {new_gate.id}")
    print("default gates created!!!")

    camera_setting_op = CameraSettingOperation(db)
    for setting in default_camera_settings:
        existing_setting = await camera_setting_op.get_one_object_name(setting.get("name"))
        if existing_setting is None:
            cam_setting_obj = CameraSettingCreate(
                name=setting["name"],
                description=setting.get("description", ""),
                value=setting["value"],
                setting_type=setting["setting_type"]
            )
            new_setting = await camera_setting_op.create_setting(cam_setting_obj)
            print(f"Created camera setting with ID: {new_setting.id}")
    print("default camera settings created!!!")

    lpr_setting_op = LprSettingOperation(db)
    for setting in default_lpr_settings:
        existing_setting = await lpr_setting_op.get_one_object_name(setting.get("name"))
        if existing_setting is None:
            lpr_setting_obj = LprSettingCreate(
                name=setting["name"],
                description=setting.get("description", ""),
                setting_type=setting["setting_type"],
                value=setting["value"],
            )
            new_setting = await lpr_setting_op.create_setting(lpr_setting_obj)
            print(f"Created lpr setting with ID: {new_setting.id}")
    print("default lpr settings created!!!")


    lpr_op = LprOperation(db)
    for lpr in default_lprs:
        db_lpr = await lpr_op.get_one_object_name(lpr["name"])
        if db_lpr:
            print("lpr object already exists.")
            # print("connecting to twisted ...")
            # await add_connection(db_lpr.id, db_lpr.ip, db_lpr.port, db_lpr.auth_token)
            return
        else:
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
            print("connecting to twisted ...")
            await add_connection(db, db_camera.id)
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
