from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserType
from settings import settings
from crud.user import UserOperation
from crud.lpr import LprOperation
from schema.user import UserCreate
from schema.lpr import LprCreate
from tcp.tcp_manager import add_connection


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
