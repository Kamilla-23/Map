# Use an image with GDAL pre-installed
FROM osgeo/gdal:ubuntu-small-3.4.1

# Set the working directory
WORKDIR /app

# Install system dependencies and Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
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
RUN gdal-config --version

# Set working directory back to /app
WORKDIR /app

# Copy the requirements file into the container
COPY app/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy the current directory contents into the container
COPY app /app

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py"]