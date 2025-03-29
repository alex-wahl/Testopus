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
    findutils \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir hatch

# Set up working directory
WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml README.md ./

# Install core dependencies directly
RUN pip install --no-cache-dir \
    pytest>=8.3.4 \
    pytest-asyncio>=0.25.3 \
    pytest-mock>=3.14.0 \
    pytest-xdist==3.6.1 \
    pytest-check==2.3.1 \
    pytest-json-report>=1.5.0 \
    selenium==4.29.0 \
    Appium-Python-Client==4.5.1 \
    playwright==1.50.0 \
    allure-pytest>=2.13.5 \
    responses>=0.25.6 \
    pydantic>=2.10.6 \
    requests>=2.31.0 \
    pytest-html>=3.2.0 \
    Faker==37.0.0 \
    pyscreenshot==3.1 \
    pyviztest==1.0.0 \
    pydantic-ai==0.0.36 \
    langchain==0.1.12 \
    pyyaml>=6.0.2 \
    python-dotenv==1.0.1

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
