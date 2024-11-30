import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.vehicle import DBVehicle

async def populate_vehicle(session: AsyncSession, car: dict) -> DBVehicle:
    """
    Populate or fetch a DBVehicle entry.
    """
    plate_number = car.get("plate", {}).get("plate", "Unknown")
    vehicle_class = json.dumps(car.get("vehicle_class", None))
    vehicle_type = json.dumps(car.get("vehicle_type", None))
    vehicle_color = json.dumps(car.get("vehicle_color", None))

    # Check if the vehicle already exists
    existing_vehicle = await session.execute(
        select(DBVehicle).where(DBVehicle.plate_number == plate_number)
    )
    vehicle = existing_vehicle.scalar_one_or_none()

    if not vehicle:
        # Create a new vehicle if it doesn't exist
        vehicle = DBVehicle(
            plate_number=plate_number,
            vehicle_class=vehicle_class,
            vehicle_type=vehicle_type,
            vehicle_color=vehicle_color,
            owner_id=None,  # No owner information available
        )
        session.add(vehicle)
        await session.commit()
        await session.refresh(vehicle)

    return vehicle
