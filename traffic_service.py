from datetime import timezone

from sqlalchemy.orm import Session

from models import (
    CameraEvent,
    CameraSegment,
    Violation
)


def process_camera_event(
    db: Session,
    vehicle_number: str,
    camera_id: int,
    captured_at,
    measured_speed: float
):

    # Find configured routes ending at this camera
    segments = db.query(CameraSegment).filter(
        CameraSegment.exit_camera_id == camera_id
    ).all()

    violations = []

    for segment in segments:

        # Find the previous entry event
        previous_event = (
            db.query(CameraEvent)
            .filter(
                CameraEvent.vehicle_number == vehicle_number,
                CameraEvent.camera_id == segment.entry_camera_id,
                CameraEvent.captured_at < captured_at
            )
            .order_by(CameraEvent.captured_at.desc())
            .first()
        )

        if previous_event is None:
            continue

        # Calculate journey duration
        elapsed_seconds = (
            captured_at - previous_event.captured_at
        ).total_seconds()

        if elapsed_seconds <= 0:
            continue

        travel_minutes = elapsed_seconds / 60

        # Calculate average speed
        elapsed_hours = elapsed_seconds / 3600

        average_speed = (
            segment.distance_km / elapsed_hours
        )

        # Check both rules
        speed_violation = (
            measured_speed > segment.speed_limit
            or average_speed > segment.speed_limit
        )

        time_violation = (
            travel_minutes < segment.min_travel_minutes
        )

        if speed_violation or time_violation:

            violation_type = []

            if measured_speed > segment.speed_limit:
                violation_type.append("INSTANT_SPEED_LIMIT")

            if average_speed > segment.speed_limit:
                violation_type.append("AVERAGE_SPEED_LIMIT")

            if time_violation:
                violation_type.append("MINIMUM_TRAVEL_TIME")

            violation = Violation(
                vehicle_number=vehicle_number,
                violation_type=", ".join(violation_type),
                average_speed=round(average_speed, 2),
                travel_time_minutes=round(travel_minutes, 2),
                status="REVIEW_REQUIRED"
            )

            db.add(violation)
            violations.append(violation)

    return violations