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

# Copy just the pyproject.toml first
COPY pyproject.toml .

# Create README.md if it doesn't exist to satisfy build dependency
RUN if [ ! -f README.md ]; then echo "# Testopus" > README.md; fi

# Install dependencies
RUN pip install -e .

# Copy rest of the code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DOCKER_ENV=true
# Configure Chrome/Chromium path for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Run tests command
CMD ["pytest", "tests"]
