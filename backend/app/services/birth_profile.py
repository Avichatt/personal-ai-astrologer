"""Birth profile application service."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.timezone import timezone_engine
from app.database.repositories.birth_profile import BirthProfileRepository
from app.schemas.birth_profile import (
    BirthProfileCreate,
    BirthProfileResponse,
    BirthProfileUpdate,
)
from app.services.geocoding import GeocodingProvider, get_geocoding_provider


class BirthProfileService:
    """Service orchestrating birth profile creation, geocoding, timezone resolution, and CRUD."""

    def __init__(
        self,
        session: AsyncSession,
        geocoding_provider: GeocodingProvider | None = None,
    ) -> None:
        self.session = session
        self.profile_repo = BirthProfileRepository(session)
        self.geocoder = geocoding_provider or get_geocoding_provider()

    async def create_profile(
        self,
        user_id: uuid.UUID,
        req: BirthProfileCreate,
    ) -> BirthProfileResponse:
        """Create and persist a new birth profile with resolved coordinates and historical UTC time."""
        lat = req.latitude
        lng = req.longitude
        city = req.city
        country = req.country
        location_name = req.location_name

        # 1. Geocode if coordinates are missing
        if lat is None or lng is None:
            geo_res = await self.geocoder.geocode(req.location_name)
            lat = geo_res.latitude
            lng = geo_res.longitude
            city = city or geo_res.city
            country = country or geo_res.country
            location_name = req.location_name or geo_res.display_name

        # 2. Timezone resolution
        tz_name = req.timezone
        if not tz_name:
            tz_name = timezone_engine.find_timezone(lat, lng)

        # 3. UTC conversion
        _, utc_dt = timezone_engine.convert_to_utc(
            birth_date=req.date_of_birth,
            local_time=req.local_time,
            tz_name=tz_name,
        )

        # 4. Handle primary profile status
        if req.is_primary:
            await self.profile_repo.clear_primary(user_id)

        # 5. Persist profile
        profile = await self.profile_repo.create(
            user_id=user_id,
            name=req.name,
            date_of_birth=req.date_of_birth,
            local_time=req.local_time,
            location_name=location_name,
            city=city,
            country=country,
            latitude=lat,
            longitude=lng,
            timezone=tz_name,
            utc_datetime=utc_dt,
            astrology_system=req.astrology_system,
            birth_time_accuracy=req.birth_time_accuracy,
            is_primary=req.is_primary,
        )
        await self.session.commit()
        return BirthProfileResponse.model_validate(profile)

    async def get_user_profiles(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[BirthProfileResponse]:
        """Fetch all birth profiles for a user."""
        profiles = await self.profile_repo.get_by_user_id(user_id, offset=offset, limit=limit)
        return [BirthProfileResponse.model_validate(p) for p in profiles]

    async def get_profile_by_id(
        self,
        user_id: uuid.UUID,
        profile_id: uuid.UUID,
    ) -> BirthProfileResponse:
        """Fetch a specific birth profile ensuring user ownership."""
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile or profile.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Birth profile not found.",
            )
        return BirthProfileResponse.model_validate(profile)

    async def update_profile(
        self,
        user_id: uuid.UUID,
        profile_id: uuid.UUID,
        req: BirthProfileUpdate,
    ) -> BirthProfileResponse:
        """Update a birth profile and recalculate timezone/UTC if date, time, or location changed."""
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile or profile.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Birth profile not found.",
            )

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return BirthProfileResponse.model_validate(profile)

        needs_recalc = any(
            k in update_data
            for k in (
                "date_of_birth",
                "local_time",
                "latitude",
                "longitude",
                "timezone",
                "location_name",
            )
        )

        if needs_recalc:
            lat = update_data.get("latitude", profile.latitude)
            lng = update_data.get("longitude", profile.longitude)
            if "location_name" in update_data and (
                "latitude" not in update_data or "longitude" not in update_data
            ):
                geo_res = await self.geocoder.geocode(update_data["location_name"])
                lat = geo_res.latitude
                lng = geo_res.longitude
                update_data["latitude"] = lat
                update_data["longitude"] = lng
                if not update_data.get("city"):
                    update_data["city"] = geo_res.city
                if not update_data.get("country"):
                    update_data["country"] = geo_res.country

            tz_name = update_data.get("timezone", profile.timezone)
            if "latitude" in update_data or "longitude" in update_data:
                tz_name = timezone_engine.find_timezone(lat, lng)
                update_data["timezone"] = tz_name

            dob = update_data.get("date_of_birth", profile.date_of_birth)
            lot = update_data.get("local_time", profile.local_time)
            _, utc_dt = timezone_engine.convert_to_utc(dob, lot, tz_name)
            update_data["utc_datetime"] = utc_dt

        if update_data.get("is_primary") is True:
            await self.profile_repo.clear_primary(user_id)

        updated_profile = await self.profile_repo.update(profile_id, **update_data)
        await self.session.commit()
        return BirthProfileResponse.model_validate(updated_profile)

    async def delete_profile(
        self,
        user_id: uuid.UUID,
        profile_id: uuid.UUID,
    ) -> bool:
        """Delete a birth profile ensuring user ownership."""
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile or profile.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Birth profile not found.",
            )
        await self.profile_repo.delete(profile_id)
        await self.session.commit()
        return True
