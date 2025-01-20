FROM python:3.13-slim
RUN apt-get update && apt-get install -y sqlite3 libsqlite3-dev
ENV POETRY_VERSION=1.5.1
RUN pip install poetry==$POETRY_VERSION
WORKDIR /app
COPY pyproject.toml .
COPY . /app
RUN poetry install --with dev
CMD ["poetry", "run", "pytest"]