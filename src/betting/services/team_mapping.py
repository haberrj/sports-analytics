from dataclasses import dataclass

from betting.models import ExternalTeamMapping
from teams.models import Team


@dataclass(frozen=True)
class TeamMappingResult:
    participants_seen: int = 0
    mappings_created: int = 0
    mappings_existing: int = 0
    mappings_unmatched: int = 0


class TeamMappingService:
    def map_participants(
        self,
        participants: dict,
    ) -> TeamMappingResult:
        created = 0
        existing = 0
        unmatched = 0

        for external_team_id, external_name in participants.items():
            team = self._find_team(external_name)

            if team is None:
                unmatched += 1
                continue

            _, was_created = ExternalTeamMapping.objects.get_or_create(
                provider=ExternalTeamMapping.Provider.ODDSPAPI,
                external_team_id=str(external_team_id),
                defaults={
                    "team": team,
                },
            )

            if was_created:
                created += 1
            else:
                existing += 1

        return TeamMappingResult(
            participants_seen=len(participants),
            mappings_created=created,
            mappings_existing=existing,
            mappings_unmatched=unmatched,
        )

    def _find_team(self, external_name: str) -> Team | None:
        normalized_external = self._normalize(external_name)

        matches = [
            team
            for team in Team.objects.all()
            if normalized_external
            in {
                self._normalize(team.name),
                self._normalize(team.city),
                self._normalize(f"{team.city} {team.name}"),
                self._normalize(team.abbreviation),
            }
        ]

        if len(matches) != 1:
            return None

        return matches[0]

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(character.lower() for character in value if character.isalnum())
