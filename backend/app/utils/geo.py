"""Geographic helpers used by the geographic-anomaly rule and the heatmap."""

from __future__ import annotations

import math

# Representative (lat, lon) coordinates for cities used by the generator.
CITY_COORDS: dict[str, tuple[float, float]] = {
    "New York": (40.7128, -74.0060),
    "Miami": (25.7617, -80.1918),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698),
    "London": (51.5074, -0.1278),
    "Frankfurt": (50.1109, 8.6821),
    "Zurich": (47.3769, 8.5417),
    "Dubai": (25.2048, 55.2708),
    "Singapore": (1.3521, 103.8198),
    "Hong Kong": (22.3193, 114.1694),
    "Tokyo": (35.6762, 139.6503),
    "Panama City": (8.9824, -79.5199),
    "George Town": (19.2866, -81.3744),  # Cayman Islands
    "Valletta": (35.8989, 14.5146),  # Malta
    "Nicosia": (35.1856, 33.3823),  # Cyprus
    "Lagos": (6.5244, 3.3792),
    "Moscow": (55.7558, 37.6173),
}

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def implied_speed_kmh(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    hours: float,
) -> float:
    """Speed required to travel between two points in ``hours``.

    Used to detect physically impossible location changes (e.g. Miami to Tokyo
    in 15 minutes implies a speed far above any aircraft).
    """
    if hours <= 0:
        return float("inf")
    return haversine_km(lat1, lon1, lat2, lon2) / hours
