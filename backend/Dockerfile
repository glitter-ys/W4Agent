FROM python:3.11-slim

# Install system dependencies for Playwright and WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright dependencies
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 libwayland-client0 \
    # WeasyPrint dependencies
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    # CJK fonts for Chinese/Japanese/Korean text rendering in screenshots
    fonts-noto-cjk \
    # General
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (non-editable, deps only)
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[dev]"

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Ensure app module is importable
ENV PYTHONPATH=/app

# Run database migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
