# Django sanity check
docker compose exec web uv run python src/manage.py check

# Check whether model changes need migrations
docker compose exec web uv run python src/manage.py makemigrations --check --dry-run

# Run all tests
docker compose exec web uv run pytest

# Run tests with coverage
docker compose exec web uv run pytest \
  --cov=src \
  --cov-report=term-missing \
  --cov-fail-under=80


docker compose exec web uv run python src/manage.py makemigrations
docker compose exec web uv run python src/manage.py migrate

uv run ruff check .
uv run ruff format --check .

docker compose exec web uv run python src/manage.py check
docker compose exec web uv run pytest \
  --cov=src \
  --cov-report=term-missing \
  --cov-fail-under=80