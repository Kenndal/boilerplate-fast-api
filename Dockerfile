# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (including curl for uv installation)
RUN apt-get update && apt-get install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (production only, no dev dependencies)
RUN uv sync --frozen

# Copy source code
COPY src/ ./src/
COPY alembic.ini ./

# Expose port 5000
EXPOSE 5000

# Run the application
CMD ["uv", "run", "uvicorn", "src.api_server.main:app", "--host", "0.0.0.0", "--port", "5000"]
