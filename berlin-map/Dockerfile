# Use the official Python 3.9 image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies and GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    python3-gdal \
    python3-dev \
    g++ \
    libgeos-dev \
    make \
    cmake \
    cython3 \
    libspatialindex-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    software-properties-common \
    build-essential \
    curl \
    ca-certificates \
    libcurl4-openssl-dev \
    libssl-dev \
    libtiff-dev \
    libsqlite3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify GDAL installation
RUN gdalinfo --version

# Set working directory back to /app
WORKDIR /app

# Copy the requirements file into the container
COPY app/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the GeoJSON files into the container
COPY app/pruned_streetlight.geojson /app/pruned_streetlight.geojson
COPY app/bezirksgrenzen.geojson /app/bezirksgrenzen.geojson

# Copy the current directory contents into the container
COPY app /app

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py"]