FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* .

COPY . .

RUN poetry config virtualenvs.create false && poetry install --only main --no-interaction --no-ansi

CMD ["uvicorn", "ad_exchange_auction.app:app", "--host", "0.0.0.0", "--port", "8000"]
