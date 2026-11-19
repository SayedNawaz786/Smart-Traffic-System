from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CameraEventCreate(BaseModel):
    vehicle_number: str = Field(min_length=5, max_length=20)
    camera_id: int
    captured_at: datetime
    measured_speed: float = Field(ge=0, le=300)

    @field_validator("captured_at")
    @classmethod
    def validate_timestamp(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must include a timezone")

        return value.astimezone(timezone.utc)


class CameraEventResponse(BaseModel):
    id: int
    vehicle_number: str
    camera_id: int
    measured_speed: float

    model_config = ConfigDict(from_attributes=True)