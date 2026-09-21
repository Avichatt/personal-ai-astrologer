"""Asynchronous Celery tasks for astrological chart calculation and rendering."""

from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="tasks.calculate_chart_async", bind=True)
def calculate_chart_async(self, birth_profile_id: str, system: str = "western") -> dict[str, str]:
    """Background task to calculate complex charts."""
    return {
        "status": "completed",
        "birth_profile_id": birth_profile_id,
        "system": system,
    }
