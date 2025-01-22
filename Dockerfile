FROM python:3.13-slim AS base

ENV POETRY_VERSION=1.5.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app
COPY pyproject.toml poetry.lock* ./

FROM base AS development
RUN poetry install --with dev

COPY . .
CMD ["poetry", "run", "pytest"]

FROM base AS production
RUN poetry install --without dev --no-root

COPY . .
RUN poetry install --only-root

CMD ["poetry", "run", "stuart"]