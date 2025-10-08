FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN uv sync --frozen

RUN mkdir -p databases secrets

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000"]



