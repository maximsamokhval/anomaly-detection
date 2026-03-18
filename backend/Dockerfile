FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --no-dev --frozen

# Copy application source
COPY src/ ./src/
COPY ui/ ./ui/
COPY scripts/ ./scripts/

# Create data and logs directories
RUN mkdir -p data logs

EXPOSE 8000

# Use the venv created by uv sync
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
