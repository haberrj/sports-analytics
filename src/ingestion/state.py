from django.utils import timezone

from games.models import Season
from ingestion.models import IngestionState


def is_complete(season: Season, dataset: str) -> bool:
    return IngestionState.objects.filter(
        league=season.league,
        season=season,
        dataset=dataset,
        last_completed_at__isnull=False,
    ).exists()


def mark_complete(season: Season, dataset: str) -> None:
    IngestionState.objects.update_or_create(
        league=season.league,
        season=season,
        dataset=dataset,
        defaults={
            "last_completed_at": timezone.now(),
        },
    )
