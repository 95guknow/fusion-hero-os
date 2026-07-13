# Fusion Hero OS - Heroic Core Docker Image
# Based on Python 3.11 slim for minimal size

FROM python:3.11-slim

LABEL maintainer="ALTE_Frau_95g Heroic Core"
LABEL version="v8"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy core modules
COPY fusion_hero_os/ ./fusion_hero_os/
COPY pyproject.toml ./
COPY docs/99_archive/MIGRATION_KONZEPT_v7.12_HardFork.md ./docs/99_archive/MIGRATION_KONZEPT_v7.12_HardFork.md

# Create non-root user for security
RUN useradd -m -u 1000 hero && chown -R hero:hero /app
USER hero

# Default command: validate core structure
CMD ["python3", "-c", "\
import os; \
print('=== Fusion Hero OS v8 Docker Container ==='); \
print('fusion_hero_os directory:', 'present' if os.path.exists('fusion_hero_os') else 'MISSING'); \
print('Migration Concept:', 'present' if os.path.exists('docs/99_archive/MIGRATION_KONZEPT_v7.12_HardFork.md') else 'MISSING'); \
print('Container ready.'); \""]
