"""Geographical coordinates model and calculation helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GeographicCoordinates:
    """Validated geographical latitude and longitude in decimal degrees."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude must be between -90 and 90 degrees, got {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(
                f"Longitude must be between -180 and 180 degrees, got {self.longitude}"
            )

    @property
    def lat_dms(self) -> str:
        """Convert latitude to Degrees Minutes Seconds formatted string."""
        deg = int(abs(self.latitude))
        minutes = int((abs(self.latitude) - deg) * 60)
        seconds = round(((abs(self.latitude) - deg) * 60 - minutes) * 60, 2)
        direction = "N" if self.latitude >= 0 else "S"
        return f"{deg}°{minutes:02d}'{seconds:05.2f}\"{direction}"

    @property
    def lng_dms(self) -> str:
        """Convert longitude to Degrees Minutes Seconds formatted string."""
        deg = int(abs(self.longitude))
        minutes = int((abs(self.longitude) - deg) * 60)
        seconds = round(((abs(self.longitude) - deg) * 60 - minutes) * 60, 2)
        direction = "E" if self.longitude >= 0 else "W"
        return f"{deg}°{minutes:02d}'{seconds:05.2f}\"{direction}"

    def distance_to(self, other: GeographicCoordinates) -> float:
        """Haversine distance in kilometers to another set of coordinates."""
        r = 6371.0  # Earth radius in km
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c
