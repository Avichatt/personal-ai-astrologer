"""Historical timezone engine using timezonefinder and zoneinfo."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from timezonefinder import TimezoneFinder


class HistoricalTimezoneEngine:
    """Accurately resolves IANA timezones and historical local-to-UTC offsets."""

    def __init__(self) -> None:
        self._tf: TimezoneFinder | None = None

    @property
    def tf(self) -> TimezoneFinder:
        """Lazy-loaded singleton for TimezoneFinder."""
        if self._tf is None:
            self._tf = TimezoneFinder()
        return self._tf

    def find_timezone(self, latitude: float, longitude: float) -> str:
        """Resolve the IANA timezone name for a given latitude and longitude.

        Falls back to 'UTC' if no timezone is found.
        """
        tz_name = self.tf.timezone_at(lat=latitude, lng=longitude)
        if not tz_name:
            # Try certain ocean/border cases with closest timezone
            tz_name = self.tf.closest_timezone_at(lat=latitude, lng=longitude)
        return tz_name or "UTC"

    def convert_to_utc(
        self,
        birth_date: date,
        local_time: time,
        tz_name: str,
    ) -> tuple[datetime, datetime]:
        """Convert local wall-clock birth date & time to a timezone-aware local datetime and UTC datetime.

        Args:
            birth_date: Date of birth (YYYY-MM-DD)
            local_time: Local wall-clock time (HH:MM:SS)
            tz_name: IANA timezone identifier (e.g., "Asia/Kolkata", "America/New_York")

        Returns:
            A tuple of (local_aware_datetime, utc_datetime)

        Raises:
            ValueError: If tz_name is invalid or date/time cannot be resolved.
        """
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as err:
            raise ValueError(f"Unknown timezone: '{tz_name}'") from err

        # Construct naive datetime
        naive_dt = datetime.combine(birth_date, local_time)

        # Attach timezone (respects historical DST rules in zoneinfo)
        local_aware_dt = naive_dt.replace(tzinfo=tz)

        # Convert to UTC
        utc_dt = local_aware_dt.astimezone(UTC)

        return local_aware_dt, utc_dt


timezone_engine = HistoricalTimezoneEngine()
