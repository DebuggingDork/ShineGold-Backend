from app.models.enums import UserRole
from app.models.user import User


def requires_location_setup(user: User) -> bool:
    """Executives must pin home location (lat/lng) on first login for farm distance sorting."""
    return user.role == UserRole.EXECUTIVE and (
        user.home_lat is None or user.home_lng is None
    )
