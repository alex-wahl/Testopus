FROM python:3.12-slim

# Set environment variables to reduce Python output buffering and ensure pip doesn't use cache
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    DOCKER_ENV=true \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install system dependencies in a single layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    curl \
    git \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir hatch

# Set up working directory
WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml README.md ./

# Pre-create all environments (use multiple cores with -j option)
RUN hatch env create -j $(nproc) test && \
    hatch env create -j $(nproc) ui && \
    hatch env create -j $(nproc) api && \
    hatch env create -j $(nproc) default

# Copy the rest of the code
COPY . .

# Default to running tests with Hatch
ENTRYPOINT ["hatch", "run"]
CMD ["test:run"]
