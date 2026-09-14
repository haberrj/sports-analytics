import pytest

from betting.models import ExternalTeamMapping
from betting.services.team_mapping import TeamMappingService
from teams.models import Team


@pytest.mark.django_db
def test_maps_participant_name_to_internal_team():
    chiefs = Team.objects.create(
        external_id="nfl-kc",
        slug="kansas-city-chiefs",
        name="Chiefs",
        abbreviation="KC",
        city="Kansas City",
    )

    participants = {
        "4422": "Kansas City Chiefs",
    }

    result = TeamMappingService().map_participants(participants)

    assert result.participants_seen == 1
    assert result.mappings_created == 1
    assert result.mappings_existing == 0
    assert result.mappings_unmatched == 0

    mapping = ExternalTeamMapping.objects.get()

    assert mapping.team == chiefs
    assert mapping.provider == ExternalTeamMapping.Provider.ODDSPAPI
    assert mapping.external_team_id == "4422"


@pytest.mark.django_db
def test_unknown_participant_is_not_mapped():
    participants = {
        "9999": "Unknown Football Team",
    }

    result = TeamMappingService().map_participants(participants)

    assert result.mappings_created == 0
    assert result.mappings_unmatched == 1
    assert ExternalTeamMapping.objects.count() == 0
