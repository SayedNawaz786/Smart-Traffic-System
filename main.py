from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import Base, engine, get_db
from models import (
    Camera,
    CameraSegment,
    CameraEvent,
    Violation
)
from schemas import CameraEventCreate
from traffic_service import process_camera_event

app = FastAPI(
    title="Smart Traffic Monitoring System",
    description="Traffic speed and travel-time violation detection API",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "Smart Traffic Monitoring System Running"
    }


# Register a traffic camera
@app.post("/cameras")
def create_camera(
    camera_name: str,
    location: str,
    db: Session = Depends(get_db)
):

    camera = Camera(
        camera_name=camera_name,
        location=location
    )

    db.add(camera)
    db.commit()
    db.refresh(camera)

    return {
        "message": "Camera registered",
        "camera_id": camera.id
    }


# Configure the road between two cameras
@app.post("/segments")
def create_segment(
    entry_camera_id: int,
    exit_camera_id: int,
    distance_km: float,
    min_travel_minutes: float,
    speed_limit: float,
    db: Session = Depends(get_db)
):

    if distance_km <= 0:
        raise HTTPException(400, "Distance must be positive")

    if entry_camera_id == exit_camera_id:
        raise HTTPException(400, "Cameras must be different")

    cameras = db.query(Camera).filter(
        Camera.id.in_([entry_camera_id, exit_camera_id])
    ).all()

    if len(cameras) != 2:
        raise HTTPException(404, "Camera not found")

    segment = CameraSegment(
        entry_camera_id=entry_camera_id,
        exit_camera_id=exit_camera_id,
        distance_km=distance_km,
        min_travel_minutes=10,
        speed_limit=60
    )

    db.add(segment)
    db.commit()
    db.refresh(segment)

    return {
        "message": "Camera route configured",
        "segment_id": segment.id,
        "distance_km": segment.distance_km,
        "speed_limit": segment.speed_limit,
        "minimum_travel_minutes": segment.min_travel_minutes
    }


# Receive vehicle data from a traffic camera
@app.post("/camera-events")
def receive_camera_event(
    data: CameraEventCreate,
    db: Session = Depends(get_db)
):

    camera = db.query(Camera).filter(
        Camera.id == data.camera_id
    ).first()

    if camera is None:
        raise HTTPException(404, "Camera not found")

    # Save camera event
    event = CameraEvent(
        vehicle_number=data.vehicle_number.upper(),
        camera_id=data.camera_id,
        captured_at=data.captured_at,
        measured_speed=data.measured_speed
    )

    db.add(event)

    # Save the event before processing it
    db.flush()

    # Execute traffic detection
    violations = process_camera_event(
        db=db,
        vehicle_number=data.vehicle_number.upper(),
        camera_id=data.camera_id,
        captured_at=data.captured_at,
        measured_speed=data.measured_speed
    )

    db.commit()

    return {
        "message": "Camera event recorded",
        "vehicle_number": data.vehicle_number,
        "violations_detected": len(violations),
        "violations": [
            {
                "type": v.violation_type,
                "average_speed": v.average_speed,
                "travel_time_minutes": v.travel_time_minutes,
                "status": v.status
            }
            for v in violations
        ]
    }


# View all possible violations
@app.get("/violations")
def get_violations(
    db: Session = Depends(get_db)
):

    records = db.query(Violation).order_by(
        desc(Violation.id)
    ).all()

    return records


# Traffic officer reviews a violation
@app.patch("/violations/{violation_id}/decision")
def review_violation(
    violation_id: int,
    decision: str,
    db: Session = Depends(get_db)
):

    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            400,
            "Decision must be APPROVED or REJECTED"
        )

    violation = db.query(Violation).filter(
        Violation.id == violation_id
    ).first()

    if violation is None:
        raise HTTPException(404, "Violation not found")

    violation.status = decision

    db.commit()

    return {
        "message": "Violation reviewed",
        "violation_id": violation.id,
        "status": violation.status
    }