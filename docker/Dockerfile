# Base image digest-pinned for reproducibility (Dependabot's docker watcher bumps it).
# chromium/chromium-driver track this pinned Debian release; exact apt-version pinning is
# deferred (brittle without a snapshot.debian.org source).
FROM python:3.14-slim@sha256:44dd04494ee8f3b538294360e7c4b3acb87c8268e4d0a4828a6500b1eff50061

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
    findutils \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir hatch

# Set up working directory
WORKDIR /app

# Copy project metadata + the source packages needed for an editable install.
# pyproject.toml is the SINGLE SOURCE OF TRUTH for dependencies — no hand-maintained list here.
COPY pyproject.toml README.md ./
COPY core ./core
COPY fixtures ./fixtures
COPY utils ./utils
COPY config ./config
COPY tests ./tests

# Install the project plus its "test" and "tools" extras straight from pyproject.toml
# (tools carries `requests`, which the internal tests' Testiny client imports).
RUN pip install --no-cache-dir -e ".[test,tools]"

# Copy the rest of the code
COPY . .

# Create empty test file to verify test discovery
RUN mkdir -p /app/tests/internal_tests && \
    echo 'def test_verify_docker_works(): assert True' > /app/tests/internal_tests/test_docker_verify.py && \
    ls -la /app/tests && \
    find /app -name "test_*.py" | sort

# Default to running with Python directly (not Hatch)
ENTRYPOINT ["python", "-m", "pytest", "--verbose"]
CMD ["tests"]
