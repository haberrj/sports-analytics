import nflreadpy as nfl


def ingest_teams():
    teams = nfl.load_teams()

    for team_data in teams.iter_rows(named=True):
        print(team_data)
