from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from database.engine import Base

class DBTraffic(Base):
    __tablename__ = "traffic"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    timestamp = Column(DateTime, default=func.now())
    ocr_accuracy = Column(Float, nullable=True)
    vision_speed = Column(Float, nullable=True)

    vehicles = relationship(
        "DBVehicle",
        secondary="traffic_vehicle_association",
        back_populates="traffic_events"
    )
