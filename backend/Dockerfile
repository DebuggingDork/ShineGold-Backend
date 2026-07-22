# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port (Render will set PORT env var)
EXPOSE 8000

# Run database migrations and start the server
CMD uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
