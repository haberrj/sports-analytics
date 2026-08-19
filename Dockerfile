FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY src ./src

EXPOSE 8000

CMD ["uv", "run", "python", "src/manage.py", "runserver", "0.0.0.0:8000"]