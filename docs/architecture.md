                        ┌───────────────┐
                        │   nflverse    │
                        │ schedules/PBP │
                        │ stats/rosters │
                        └───────┬───────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   INGESTION     │
                       │ Django command  │
                       └────────┬────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │ PostgreSQL  │
                         └──────┬──────┘
                                │
                 ┌──────────────┴───────────────┐
                 │                              │
                 ▼                              ▼
        ┌─────────────────┐           ┌─────────────────┐
        │ Feature Engine  │           │ Fantasy Engine  │
        │ rolling stats   │           │ players/matchup │
        │ opponent adjust │           │ DEF streaming   │
        │ Elo/etc.        │           │ draft value     │
        └────────┬────────┘           └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │   ML Models     │
        │ winner          │
        │ margin          │
        │ total           │
        └────────┬────────┘
                 │
                 ▼
      ┌──────────────────────┐
      │ Prediction / Sim     │
      │ Monte Carlo games    │
      │ probabilities        │
      └──────────┬───────────┘
                 │
                 │     ┌──────────────┐
                 ├─────│ Odds source  │
                 │     └──────────────┘
                 ▼
          ┌─────────────┐
          │ Django UI   │
          └─────────────┘