# syntax=docker/dockerfile:1
FROM python:3.10-bullseye

# Expose the required port for Vertex AI
EXPOSE 8080
ENV PORT 8080

# Set up working directory
WORKDIR /app

# Install system dependencies, clean up cache to keep image size small
RUN apt update && \
    apt install -y -qq ffmpeg && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Create required directories
RUN mkdir -p /app/logs/weights/RVC && \
    mkdir -p /app/assets/tts

# Copy application files into the container
COPY . .

# Copy RVC models
COPY logs/weights/RVC/Morgan-Freeman.pth /app/logs/weights/RVC/
COPY logs/weights/RVC/added_IVF455_Flat_nprobe_1_Morgan-Freeman_v2.index /app/logs/weights/RVC/

# Create a virtual environment in the app directory and install dependencies
RUN python3 -m venv /app/.venv && \
    . /app/.venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir python-ffmpeg && \
    pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121 && \
    if [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi

# Define volumes for persistent storage
VOLUME ["/app/logs/", "/app/assets/"]

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV APPLIO_API_WRITE=""

# Run the FastAPI app
ENTRYPOINT ["python3"]
CMD ["main.py"]
