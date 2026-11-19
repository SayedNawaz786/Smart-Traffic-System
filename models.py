from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)

from database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)

    camera_name = Column(String(100), nullable=False)

    location = Column(String(200))


class CameraSegment(Base):
    __tablename__ = "camera_segments"

    id = Column(Integer, primary_key=True)

    entry_camera_id = Column(
        Integer,
        ForeignKey("cameras.id"),
        nullable=False
    )

    exit_camera_id = Column(
        Integer,
        ForeignKey("cameras.id"),
        nullable=False
    )

    distance_km = Column(Float, nullable=False)

    min_travel_minutes = Column(Float, default=10.0)

    speed_limit = Column(Float, default=60.0)


class CameraEvent(Base):
    __tablename__ = "camera_events"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_number = Column(String(20), index=True)

    camera_id = Column(Integer, ForeignKey("cameras.id"))

    captured_at = Column(DateTime(timezone=True))

    measured_speed = Column(Float)


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_number = Column(String(20))

    violation_type = Column(String(100))

    average_speed = Column(Float)

    travel_time_minutes = Column(Float)

    status = Column(String(50), default="REVIEW_REQUIRED")

    fine_amount = Column(Float, nullable=True)