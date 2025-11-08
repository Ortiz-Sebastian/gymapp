# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies required for OpenCV, PostgreSQL, PostGIS, and ML models
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    libgeos-dev \
    libproj-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Find and verify GDAL library path for Django (works for both x86_64 and ARM64)
RUN \
    echo "=== Finding GDAL library ===" && \
    # Check what architecture we're on
    ARCH=$(dpkg --print-architecture) && \
    echo "Architecture: $ARCH" && \
    # Find the actual library file (may have version number like libgdal.so.33)
    GDAL_LIB_PATH=$(find /usr/lib -name "libgdal.so*" -type f 2>/dev/null | head -1) && \
    if [ -z "$GDAL_LIB_PATH" ]; then \
        echo "Trying alternative search..." && \
        GDAL_LIB_PATH=$(find /usr -name "libgdal.so*" -type f 2>/dev/null | head -1); \
    fi && \
    if [ -n "$GDAL_LIB_PATH" ]; then \
        echo "✅ GDAL library found at: $GDAL_LIB_PATH" && \
        ls -lh "$GDAL_LIB_PATH" && \
        # Create symlink without version if it doesn't exist (for Django compatibility)
        GDAL_DIR=$(dirname "$GDAL_LIB_PATH") && \
        GDAL_BASE=$(basename "$GDAL_LIB_PATH" | sed 's/\.[0-9]*$//') && \
        if [ ! -f "$GDAL_DIR/$GDAL_BASE" ] && [ "$GDAL_LIB_PATH" != "$GDAL_DIR/$GDAL_BASE" ]; then \
            echo "Creating symlink: $GDAL_DIR/$GDAL_BASE -> $GDAL_LIB_PATH" && \
            ln -sf "$(basename "$GDAL_LIB_PATH")" "$GDAL_DIR/$GDAL_BASE" || true; \
        fi && \
        echo "export GDAL_LIBRARY_PATH=$GDAL_LIB_PATH" >> /etc/profile.d/gdal.sh && \
        echo "$GDAL_LIB_PATH" > /tmp/gdal_lib_path.txt; \
    else \
        echo "❌ Warning: GDAL library not found!" && \
        echo "Checking installed packages..." && \
        dpkg -L libgdal-dev 2>/dev/null | grep -E "libgdal|\.so" || true && \
        echo "All libgdal files:" && \
        find /usr -name "*gdal*" -type f 2>/dev/null | head -10 || true; \
    fi

# Set GDAL library path as environment variable
# Will be dynamically found at runtime if not set
ENV GDAL_LIBRARY_PATH=""

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create directory for ML models (will be populated at runtime)
RUN mkdir -p /app/ml_models

# Collect static files
WORKDIR /app/gymReview
RUN python manage.py collectstatic --noinput || true

# Reset workdir to /app for commands
WORKDIR /app

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "cd gymReview && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

