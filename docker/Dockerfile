FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    git \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy project files for dependency installation
COPY pyproject.toml README.md ./

# Install Hatch
RUN pip install --no-cache-dir hatch

# Pre-create all environments and install dependencies to avoid reinstalling each run
RUN hatch env create test && \
    hatch env create ui && \
    hatch env create api && \
    hatch env create default

# Copy the rest of the code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DOCKER_ENV=true
# Configure Chrome/Chromium path for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Default to running tests with Hatch
ENTRYPOINT ["hatch", "run"]
CMD ["test:run"]
