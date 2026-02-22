"""
Location utilities for Outpass Management System.
Haversine formula for distance calculation.
"""

import math
from decimal import Decimal


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two points in meters using Haversine formula.
    """
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_within_radius(
    user_lat: float,
    user_lon: float,
    location_lat: float,
    location_lon: float,
    allowed_radius_meters: int,
) -> bool:
    """
    Check if user coordinates are within allowed radius of the location.
    """
    distance = haversine_distance(
        user_lat, user_lon, float(location_lat), float(location_lon)
    )
    return distance <= allowed_radius_meters
