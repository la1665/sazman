from sqlalchemy import Column, String, Integer, Float, DateTime, func

from database.engine import Base


class DBTraffic(Base):
    __tablename__ = "traffic"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, index=True)
    camera_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=func.now())
    ocr_accuracy = Column(String, nullable=True)
    vision_speed = Column(String, nullable=True)

    # vehicles = relationship(
    #     "DBVehicle",
    #     secondary="traffic_vehicle_association",
    #     back_populates="traffic_events"
    # )
