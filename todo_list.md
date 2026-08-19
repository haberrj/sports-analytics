# NFL Analysis — Branch Roadmap & To-Do List

This roadmap assumes the branch model:

```text
feature/* → develop → master
```

`develop` is the integration branch for completed features.
`master` is the stable/releasable branch.

---

## Completed

* [x] `feature/core-models`

  * [x] Create league/conference/division/team models
  * [x] Create season/week/game models
  * [x] Create `TeamSeason`
  * [x] Add NFL team game stats
  * [x] Add NFL player model
  * [x] Add NFL player game stats
  * [x] Add point-in-time player availability/injury status
  * [x] Add domain validation
  * [x] Add database constraints
  * [x] Add migrations
  * [x] Add model tests
  * [x] Add Ruff exclusions for migrations
  * [x] Add pytest coverage
  * [x] Add coverage threshold
  * [x] Add coverage output to GitHub Actions summary
  * [x] Upload coverage artifacts in CI
  * [x] Merge into `develop`

---

# Phase 1 — Data Foundation

## `feature/nfl-data-ingestion`

* [ ] Add NFL data-source dependency
* [ ] Evaluate `nflreadpy` / nflverse datasets
* [ ] Create NFL integration/service layer
* [ ] Add ingestion configuration
* [ ] Import NFL league
* [ ] Import AFC/NFC conferences
* [ ] Import divisions
* [ ] Import NFL teams
* [ ] Generate stable team slugs
* [ ] Import seasons
* [ ] Import weeks
* [ ] Import historical games
* [ ] Map source game IDs to `Game.external_id`
* [ ] Populate home/away teams
* [ ] Populate kickoff timestamps
* [ ] Populate scores
* [ ] Populate game status
* [ ] Populate overtime/finish information where available
* [ ] Create `TeamSeason` memberships
* [ ] Ensure ingestion is idempotent
* [ ] Add management command for ingestion
* [ ] Add ingestion tests
* [ ] Add malformed-source-data handling
* [ ] Add logging
* [ ] Add ingestion summary output

Suggested command:

```text
python manage.py ingest_nfl
```

---

## `feature/nfl-team-stats-ingestion`

* [ ] Determine nflverse source fields for team game stats
* [ ] Map source data into `NFLTeamGameStats`
* [ ] Populate:

  * [ ] points for
  * [ ] points allowed
  * [ ] passing yards
  * [ ] passing attempts
  * [ ] passing completions
  * [ ] rushing yards
  * [ ] rushing attempts
  * [ ] sacks allowed
  * [ ] defensive sacks
  * [ ] first downs
  * [ ] third-down attempts
  * [ ] third-down conversions
  * [ ] fourth-down attempts
  * [ ] fourth-down conversions
  * [ ] penalties
  * [ ] penalty yards
  * [ ] turnovers
  * [ ] turnovers forced
  * [ ] field goals attempted
  * [ ] field goals made
* [ ] Validate game/team consistency
* [ ] Validate mirrored offensive/defensive data
* [ ] Prevent duplicate stats imports
* [ ] Add team-stat ingestion tests
* [ ] Add management command or integrate into main ingestion command

---

## `feature/nfl-player-ingestion`

* [ ] Import NFL players
* [ ] Map nflverse player IDs to `NFLPlayer.external_id`
* [ ] Map NFL positions
* [ ] Handle generic `OL`, `DL`, `DB`
* [ ] Handle inactive players
* [ ] Handle player renames/name changes if necessary
* [ ] Import player game stats
* [ ] Populate passing stats
* [ ] Populate rushing stats
* [ ] Populate receiving stats
* [ ] Populate kicking stats
* [ ] Validate team/game association
* [ ] Add player ingestion tests
* [ ] Ensure player imports are idempotent

---

## `feature/nfl-injury-ingestion`

* [ ] Identify reliable injury/status source
* [ ] Import injury reports
* [ ] Map player to team/game
* [ ] Populate statuses:

  * [ ] active
  * [ ] questionable
  * [ ] doubtful
  * [ ] out
  * [ ] IR
* [ ] Determine whether additional statuses are required
* [ ] Preserve `captured_at`
* [ ] Prevent future information leaking into historical snapshots
* [ ] Support multiple snapshots for a player/game
* [ ] Identify expected starters where possible
* [ ] Add injury ingestion tests

---

# Phase 2 — Historical Data & Feature Engineering

## `feature/historical-backfill`

* [ ] Decide initial historical range
* [ ] Backfill NFL seasons
* [ ] Backfill games
* [ ] Backfill team game stats
* [ ] Backfill players
* [ ] Backfill player game stats
* [ ] Backfill injury data where historically available
* [ ] Validate record counts by season
* [ ] Validate team schedules
* [ ] Detect duplicate games
* [ ] Detect missing games
* [ ] Add historical-data health report
* [ ] Add backfill command

---

## `feature/team-feature-engine`

* [ ] Create analytics package
* [ ] Separate raw stats from derived features
* [ ] Create point-in-time feature API
* [ ] Implement season-to-date aggregates
* [ ] Implement rolling 3-game features
* [ ] Implement rolling 5-game features
* [ ] Implement rolling season features
* [ ] Derive:

  * [ ] completion percentage
  * [ ] passing yards per attempt
  * [ ] rushing yards per attempt
  * [ ] total yards
  * [ ] third-down percentage
  * [ ] fourth-down percentage
  * [ ] field-goal percentage
  * [ ] turnover differential
  * [ ] sack differential
  * [ ] point differential
  * [ ] penalties/game
  * [ ] penalty yards/game
* [ ] Calculate offensive features
* [ ] Calculate defensive features
* [ ] Calculate home/away splits
* [ ] Calculate division/conference splits
* [ ] Ensure no future-game leakage
* [ ] Add feature tests with known historical cutoffs

---

## `feature/elo-ratings`

* [ ] Implement Elo baseline
* [ ] Add configurable starting Elo
* [ ] Add home-field adjustment
* [ ] Update ratings chronologically
* [ ] Persist or reconstruct historical Elo
* [ ] Add preseason regression-to-mean
* [ ] Test Elo against historical games
* [ ] Make Elo available as ML feature
* [ ] Make Elo available as benchmark model

---

## `feature/player-strength-features`

* [ ] Build player-strength framework
* [ ] Start with quarterbacks
* [ ] Calculate QB rolling metrics
* [ ] Calculate:

  * [ ] passing efficiency
  * [ ] yards/attempt
  * [ ] completion rate
  * [ ] interception rate
  * [ ] sack rate
  * [ ] rushing contribution
* [ ] Add EPA/CPOE if available
* [ ] Create starting-QB feature
* [ ] Calculate QB strength differential
* [ ] Handle backup QB situations
* [ ] Add player availability penalties
* [ ] Explore non-QB player strength
* [ ] Add tests preventing future-data leakage

---

## `feature/injury-features`

* [ ] Convert player status snapshots into game features
* [ ] Determine player importance weighting
* [ ] Calculate unavailable-player strength
* [ ] Calculate expected lineup strength
* [ ] Distinguish starter vs depth player
* [ ] Create offense injury score
* [ ] Create defense injury score
* [ ] Create QB availability feature
* [ ] Ensure feature generation uses latest snapshot before prediction time
* [ ] Add historical injury-feature tests

---

# Phase 3 — Machine Learning

## `feature/ml-dataset`

* [ ] Build historical game feature dataset
* [ ] One row per historical game
* [ ] Generate home/away feature differences
* [ ] Add team features
* [ ] Add Elo
* [ ] Add QB features
* [ ] Add injury features
* [ ] Add rest days
* [ ] Add home-field indicator
* [ ] Add neutral-site indicator
* [ ] Add division-game indicator
* [ ] Add conference-game indicator
* [ ] Add outcome labels
* [ ] Add point-margin labels
* [ ] Add total-score labels
* [ ] Add dataset validation
* [ ] Export/debug sample feature rows
* [ ] Guarantee chronological point-in-time construction

---

## `feature/ml-baselines`

* [ ] Implement home-team baseline
* [ ] Implement Elo prediction baseline
* [ ] Implement logistic regression
* [ ] Train historical model
* [ ] Evaluate accuracy
* [ ] Evaluate Brier score
* [ ] Evaluate log loss
* [ ] Evaluate calibration
* [ ] Store model metadata
* [ ] Version models
* [ ] Add tests around training pipeline

---

## `feature/ml-tree-models`

* [ ] Add Random Forest
* [ ] Add XGBoost or LightGBM
* [ ] Define hyperparameter configuration
* [ ] Train chronologically
* [ ] Compare against logistic regression
* [ ] Compare against Elo
* [ ] Evaluate overfitting
* [ ] Evaluate feature importance
* [ ] Store training results
* [ ] Select initial production model

---

## `feature/margin-total-models`

* [ ] Build expected-margin regression model
* [ ] Build expected-total model
* [ ] Consider separate home/away scoring models
* [ ] Evaluate MAE
* [ ] Evaluate RMSE
* [ ] Compare predicted margin to actual margin
* [ ] Compare predicted totals to actual totals
* [ ] Version models independently

---

## `feature/model-calibration`

* [ ] Add calibration curves
* [ ] Evaluate probability buckets
* [ ] Add Platt/isotonic calibration if needed
* [ ] Store calibrated model
* [ ] Compare calibrated vs raw probabilities
* [ ] Add calibration tests

---

## `feature/model-registry`

* [ ] Add prediction model database models
* [ ] Store model name/version
* [ ] Store training window
* [ ] Store hyperparameters
* [ ] Store feature list
* [ ] Store evaluation metrics
* [ ] Mark production model
* [ ] Support candidate models
* [ ] Add model promotion rules
* [ ] Prevent automatic promotion solely because training succeeded

---

# Phase 4 — Prediction & Backtesting

## `feature/game-predictions`

* [ ] Add `GamePrediction` model
* [ ] Store model version
* [ ] Store creation timestamp
* [ ] Store win probability
* [ ] Store expected margin
* [ ] Store expected total
* [ ] Store expected home score
* [ ] Store expected away score
* [ ] Store feature snapshot/reference
* [ ] Generate predictions for arbitrary game
* [ ] Generate predictions for full week
* [ ] Add prediction tests

---

## `feature/prediction-snapshots`

* [ ] Preserve predictions historically
* [ ] Never overwrite prior predictions
* [ ] Support multiple predictions for same game
* [ ] Track prediction timestamp
* [ ] Track injury-state timestamp
* [ ] Track model version
* [ ] Make historical prediction reproducible
* [ ] Add snapshot tests

---

## `feature/backtesting`

* [ ] Build chronological backtest engine
* [ ] Predict week N using only data before week N
* [ ] Advance one week at a time
* [ ] Record predictions
* [ ] Compare to actual results
* [ ] Measure:

  * [ ] accuracy
  * [ ] Brier score
  * [ ] log loss
  * [ ] calibration
  * [ ] margin MAE
  * [ ] total MAE
* [ ] Break results down by season
* [ ] Break results down by confidence
* [ ] Compare models
* [ ] Add backtest reports
* [ ] Add backtest tests

---

# Phase 5 — Simulation

## `feature/game-simulation`

* [ ] Design score distribution methodology
* [ ] Implement Monte Carlo simulation
* [ ] Simulate win probability
* [ ] Simulate point margin
* [ ] Simulate total
* [ ] Simulate spread coverage
* [ ] Configure simulation count
* [ ] Record simulation results
* [ ] Validate simulation against direct model probabilities
* [ ] Add deterministic seeds for tests

---

# Phase 6 — Odds & Betting

## `feature/odds-models`

* [ ] Add sportsbook model
* [ ] Add odds snapshot model
* [ ] Store captured timestamp
* [ ] Store moneyline
* [ ] Store spread
* [ ] Store total
* [ ] Support multiple sportsbooks
* [ ] Preserve line movement
* [ ] Add odds validation

---

## `feature/odds-ingestion`

* [ ] Select odds provider
* [ ] Prefer structured API over scraping
* [ ] Add odds integration abstraction
* [ ] Match sportsbook game to internal `Game`
* [ ] Store opening odds
* [ ] Store updates
* [ ] Store closing odds
* [ ] Add idempotent imports
* [ ] Add odds ingestion tests

---

## `feature/market-probabilities`

* [ ] Convert American odds to implied probability
* [ ] Convert decimal odds to implied probability
* [ ] Handle vig
* [ ] Calculate normalized market probabilities
* [ ] Compare model vs market
* [ ] Calculate probability edge
* [ ] Add conversion unit tests

---

## `feature/betting-ev`

* [ ] Calculate expected value
* [ ] Calculate expected ROI
* [ ] Calculate model edge
* [ ] Add configurable minimum edge
* [ ] Implement `NO BET`
* [ ] Implement value categories
* [ ] Add optional fractional Kelly calculation
* [ ] Add bankroll simulation later if useful
* [ ] Test all EV calculations

---

## `feature/betting-backtest`

* [ ] Backtest model against historical odds
* [ ] Track hypothetical wagers
* [ ] Track ROI
* [ ] Track win/loss record
* [ ] Track maximum drawdown
* [ ] Track closing-line value
* [ ] Compare model versions
* [ ] Test different minimum-edge thresholds
* [ ] Guard against hindsight bias

---

# Phase 7 — Django Frontend

## `feature/base-frontend`

* [ ] Create base Django templates
* [ ] Add navigation
* [ ] Add site layout
* [ ] Add static assets
* [ ] Add responsive layout
* [ ] Add dashboard route
* [ ] Add basic error pages

---

## `feature/current-week-dashboard`

* [ ] Display current season/week
* [ ] Show upcoming games
* [ ] Show home/away teams
* [ ] Show win probabilities
* [ ] Show expected scores
* [ ] Show expected margin
* [ ] Show betting-market comparison
* [ ] Show recommendation
* [ ] Link to matchup detail pages

---

## `feature/matchup-detail`

* [ ] Add individual matchup page
* [ ] Show team comparison
* [ ] Show model probability
* [ ] Show expected score
* [ ] Show margin
* [ ] Show total
* [ ] Show odds
* [ ] Show model edge
* [ ] Show injuries
* [ ] Show QB comparison
* [ ] Show simulations
* [ ] Show historical matchup context where useful

---

## `feature/team-simulator`

* [ ] Add home-team dropdown
* [ ] Add away-team dropdown
* [ ] Add season/week selection
* [ ] Validate same-team selection
* [ ] Generate prediction
* [ ] Generate simulation
* [ ] Display key features
* [ ] Display probability
* [ ] Display expected score
* [ ] Display confidence

---

## `feature/team-pages`

* [ ] Add team detail page
* [ ] Show season record
* [ ] Show recent games
* [ ] Show offensive statistics
* [ ] Show defensive statistics
* [ ] Show Elo
* [ ] Show current form
* [ ] Show injury summary
* [ ] Show upcoming games
* [ ] Show historical predictions

---

## `feature/model-dashboard`

* [ ] Show current production model
* [ ] Show model versions
* [ ] Show training dates
* [ ] Show metrics
* [ ] Show accuracy
* [ ] Show Brier score
* [ ] Show log loss
* [ ] Show calibration
* [ ] Show feature importance
* [ ] Show model comparison

---

## `feature/backtest-dashboard`

* [ ] Show historical model performance
* [ ] Filter by season
* [ ] Filter by model
* [ ] Show calibration
* [ ] Show prediction accuracy
* [ ] Show margin error
* [ ] Show betting ROI
* [ ] Show closing-line value

---

# Phase 8 — Explainability

## `feature/model-explainability`

* [ ] Add logistic coefficients display
* [ ] Add SHAP for tree models
* [ ] Calculate per-game feature contributions
* [ ] Display factors helping home team
* [ ] Display factors helping away team
* [ ] Show injury impact
* [ ] Show QB impact
* [ ] Avoid misleading causal wording
* [ ] Add explainability tests

---

# Phase 9 — Automation

## `feature/scheduled-ingestion`

* [ ] Add scheduled data update mechanism
* [ ] Refresh completed games
* [ ] Refresh stats
* [ ] Refresh player data
* [ ] Refresh injuries
* [ ] Refresh odds
* [ ] Add job logging
* [ ] Add retry strategy
* [ ] Add failure reporting

---

## `feature/model-retraining`

* [ ] Add scheduled training job
* [ ] Rebuild training dataset
* [ ] Train candidate models
* [ ] Evaluate candidate models
* [ ] Compare to production
* [ ] Store metrics
* [ ] Require promotion criteria
* [ ] Generate predictions after approved model update

---

## `feature/prediction-refresh`

* [ ] Refresh predictions after game completion
* [ ] Refresh after injury updates
* [ ] Refresh after major lineup change
* [ ] Refresh after odds updates where appropriate
* [ ] Preserve all prior snapshots
* [ ] Prevent accidental overwrite

---

# Phase 10 — Deployment

## `feature/production-docker`

* [ ] Replace Django dev server with production server
* [ ] Add Gunicorn or suitable ASGI server
* [ ] Remove development-only mounts
* [ ] Add production environment settings
* [ ] Add healthchecks
* [ ] Harden Docker image
* [ ] Ensure reproducible UV installation
* [ ] Add image-build CI test

---

## `feature/vps-deployment`

* [ ] Configure VPS deployment
* [ ] Configure persistent Postgres volume
* [ ] Configure environment secrets
* [ ] Configure Cloudflare Tunnel
* [ ] Remove public Postgres port
* [ ] Configure restart policies
* [ ] Configure backups
* [ ] Configure log rotation
* [ ] Verify migrations during deployment
* [ ] Add deployment documentation

---

## `feature/deployment-ci`

* [ ] Build Docker image in CI
* [ ] Run production-image smoke test
* [ ] Optionally publish image
* [ ] Add deployment workflow
* [ ] Restrict deployment to `master`
* [ ] Require passing CI
* [ ] Add rollback strategy

---

# Phase 11 — Fantasy Football

## `feature/fantasy-player-models`

* [ ] Revisit roster/player membership model
* [ ] Model trades
* [ ] Model waivers
* [ ] Model free agents
* [ ] Model depth charts
* [ ] Model active/inactive status
* [ ] Add fantasy-specific player data

---

## `feature/fantasy-projections`

* [ ] Build QB projections
* [ ] Build RB projections
* [ ] Build WR projections
* [ ] Build TE projections
* [ ] Build K projections if desired
* [ ] Build DST projections
* [ ] Evaluate historical projection error

---

## `feature/fantasy-draft-data`

* [ ] Identify ADP/ranking source
* [ ] Import consensus rankings
* [ ] Import ADP
* [ ] Store ranking snapshots
* [ ] Compare internal projection vs ADP
* [ ] Calculate value difference

---

## `feature/fantasy-draft-analysis`

* [ ] Calculate draft targets
* [ ] Calculate avoids
* [ ] Add positional scarcity
* [ ] Add value over replacement
* [ ] Add roster-construction logic
* [ ] Add draft dashboard

---

## `feature/defense-streaming`

* [ ] Build DST-specific feature dataset
* [ ] Add opponent sacks allowed
* [ ] Add opponent turnover rate
* [ ] Add QB quality
* [ ] Add offensive-line performance
* [ ] Add defensive pressure
* [ ] Add implied points
* [ ] Build DST projection model
* [ ] Rank available defenses
* [ ] Add weekly streaming dashboard

---

# Phase 12 — Polish & Expansion

## `feature/data-quality-dashboard`

* [ ] Show missing games
* [ ] Show incomplete stats
* [ ] Show ingestion failures
* [ ] Show stale injuries
* [ ] Show stale odds
* [ ] Show duplicate detection
* [ ] Show last successful sync

---

## `feature/admin-improvements`

* [ ] Register useful models in Django admin
* [ ] Add search
* [ ] Add filters
* [ ] Add read-only computed fields
* [ ] Add bulk operations where safe

---

## `feature/performance`

* [ ] Profile slow queries
* [ ] Add indexes based on actual access patterns
* [ ] Add `select_related` / `prefetch_related`
* [ ] Cache expensive derived calculations
* [ ] Optimize historical feature generation
* [ ] Benchmark backtests

---

## `feature/security-hardening`

* [ ] Production secret handling
* [ ] Allowed hosts
* [ ] CSRF configuration
* [ ] Secure cookies
* [ ] Rate limiting if public
* [ ] Authentication if needed
* [ ] Dependency scanning
* [ ] Container scanning

---

## `feature/multi-sport-foundation`

* [ ] Revisit existing tech debt around multi-sport assumptions
* [ ] Review generic scheduling abstractions
* [ ] Review standings rules
* [ ] Review game-result representation
* [ ] Review team/player identity
* [ ] Review league-specific stats architecture
* [ ] Decide whether another sport warrants new abstractions
* [ ] Avoid changing generic models until a real second sport requires it

---

# Release Milestones

## `develop → master` — Alpha

* [ ] Historical NFL ingestion works
* [ ] Current game ingestion works
* [ ] Team features work
* [ ] Elo works
* [ ] Logistic regression works
* [ ] Historical backtesting works
* [ ] Basic Django prediction UI works
* [ ] CI green
* [ ] Docker deployment works

---

## `develop → master` — Beta

* [ ] Player strength included
* [ ] Injury snapshots included
* [ ] Tree model included
* [ ] Simulation works
* [ ] Odds ingestion works
* [ ] Model-vs-market comparison works
* [ ] Betting backtesting works
* [ ] Model dashboard works
* [ ] VPS deployment stable

---

## `develop → master` — v1

* [ ] Automated weekly ingestion
* [ ] Automated prediction refresh
* [ ] Model versioning
* [ ] Model explainability
* [ ] Historical prediction snapshots
* [ ] Stable betting dashboard
* [ ] Stable matchup simulator
* [ ] Monitoring/data-quality checks
* [ ] Backups
* [ ] Production deployment documentation

---

# Suggested Immediate Sequence

* [x] `feature/core-models`
* [ ] `feature/nfl-data-ingestion`
* [ ] `feature/nfl-team-stats-ingestion`
* [ ] `feature/nfl-player-ingestion`
* [ ] `feature/nfl-injury-ingestion`
* [ ] `feature/historical-backfill`
* [ ] `feature/team-feature-engine`
* [ ] `feature/elo-ratings`
* [ ] `feature/player-strength-features`
* [ ] `feature/ml-dataset`
* [ ] `feature/ml-baselines`
* [ ] `feature/ml-tree-models`
* [ ] `feature/game-predictions`
* [ ] `feature/backtesting`
* [ ] `feature/game-simulation`
* [ ] `feature/odds-models`
* [ ] `feature/odds-ingestion`
* [ ] `feature/betting-ev`
* [ ] `feature/base-frontend`
* [ ] `feature/current-week-dashboard`
* [ ] `feature/matchup-detail`
* [ ] `feature/team-simulator`
* [ ] `feature/model-explainability`
* [ ] `feature/scheduled-ingestion`
* [ ] `feature/production-docker`
* [ ] `feature/vps-deployment`
* [ ] Fantasy work after the core betting/prediction platform is stable
