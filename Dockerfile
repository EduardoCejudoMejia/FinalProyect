FROM python:3.12-slim AS builder
WORKDIR /app
ENV POETRY_VIRTUALENVS_CREATE=false POETRY_NO_INTERACTION=1
RUN pip install --no-cache-dir poetry==2.4.1
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-root

FROM python:3.12-slim
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /usr/local /usr/local
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
USER app
EXPOSE 8000
CMD ["uvicorn", "practica_final.api:app", "--host", "0.0.0.0", "--port", "8000"]
