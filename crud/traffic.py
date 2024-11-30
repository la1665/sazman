from datetime import datetime
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from models.traffic import DBTraffic
from models.association import traffic_vehicle_association


async def populate_traffic(session: AsyncSession, camera_id: str, vehicles: list, timestamp: str = None) -> DBTraffic:
    """
    Populate a DBTraffic entry.
    """
    # Parse the timestamp string into a naive datetime object
    if timestamp:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
    else:
        parsed_timestamp = datetime.utcnow()
    # Create a new traffic entry
    traffic = DBTraffic(
        camera_id=camera_id,
        timestamp=parsed_timestamp,
    )
    session.add(traffic)
    await session.flush()  # Flush to generate the ID for association

    # Associate the traffic event with vehicles
    for vehicle in vehicles:
        await session.execute(
            traffic_vehicle_association.insert().values(traffic_id=traffic.id, vehicle_id=vehicle.id)
        )

    await session.commit()
    await session.refresh(traffic)

    return traffic
