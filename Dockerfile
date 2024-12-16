# syntax=docker/dockerfile:1
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    curl \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir python-ffmpeg && \
    pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir gunicorn google-cloud-storage && \
    if [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application files
COPY . .

# Create required directories
RUN mkdir -p logs assets/audios rvc/models/pretraineds rvc/models/embedders rvc/models/predictors

# Set environment variables for performance
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1

# Define volumes for persistent storage
VOLUME ["/app/logs", "/app/assets/audios", "/app/rvc/models"]

# Expose port
EXPOSE 8000

# Run with gunicorn for production
CMD [".venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "12", "--timeout", "300", "--preload", "assets.flask.routes:app"]
