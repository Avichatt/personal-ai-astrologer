"""Geocoding service provider abstraction and implementations."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config.settings import get_settings


@dataclass
class GeocodingResult:
    """Standardized geocoding result."""

    latitude: float
    longitude: float
    display_name: str
    city: str | None = None
    country: str | None = None
    raw: dict[str, Any] | None = None


class GeocodingProvider(abc.ABC):
    """Abstract base class for geocoding service providers."""

    @abc.abstractmethod
    async def geocode(self, query: str) -> GeocodingResult:
        """Geocode a place or address query to coordinates and place metadata."""
        pass


class NominatimGeocodingProvider(GeocodingProvider):
    """OpenStreetMap Nominatim geocoder implementation."""

    BASE_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, user_agent: str | None = None) -> None:
        settings = get_settings()
        self.user_agent = user_agent or settings.nominatim_user_agent

    async def geocode(self, query: str) -> GeocodingResult:
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location query cannot be empty.",
            )

        headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "en",
        }
        params = {
            "q": query.strip(),
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 1,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            except Exception as err:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Geocoding service unavailable: {err}",
                ) from err

        if not data or len(data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not resolve location: '{query}'. Please provide more specific city/country details.",
            )

        item = data[0]
        address = item.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
        )
        country = address.get("country")

        return GeocodingResult(
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            display_name=item.get("display_name", query),
            city=city,
            country=country,
            raw=item,
        )


class MockGeocodingProvider(GeocodingProvider):
    """Mock geocoder for tests and development without external HTTP dependencies."""

    KNOWN_LOCATIONS: dict[str, GeocodingResult] = {
        "kolkata": GeocodingResult(
            latitude=22.5726,
            longitude=88.3639,
            display_name="Kolkata, West Bengal, India",
            city="Kolkata",
            country="India",
        ),
        "new york": GeocodingResult(
            latitude=40.7128,
            longitude=-74.0060,
            display_name="New York, NY, USA",
            city="New York",
            country="United States",
        ),
        "london": GeocodingResult(
            latitude=51.5074,
            longitude=-0.1278,
            display_name="London, Greater London, England, United Kingdom",
            city="London",
            country="United Kingdom",
        ),
        "tokyo": GeocodingResult(
            latitude=35.6762,
            longitude=139.6503,
            display_name="Tokyo, Japan",
            city="Tokyo",
            country="Japan",
        ),
    }

    async def geocode(self, query: str) -> GeocodingResult:
        normalized = query.strip().lower()
        for key, res in self.KNOWN_LOCATIONS.items():
            if key in normalized:
                return res
        # Default fallback coordinates (0,0) or match
        return GeocodingResult(
            latitude=28.6139,
            longitude=77.2090,
            display_name=f"{query} (Resolved)",
            city="New Delhi",
            country="India",
        )


def get_geocoding_provider() -> GeocodingProvider:
    """Factory to retrieve configured geocoding provider."""
    settings = get_settings()
    if settings.is_testing:
        return MockGeocodingProvider()
    return NominatimGeocodingProvider()
