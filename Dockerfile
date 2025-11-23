# Railway Dockerfile for Financial Analysis App
# Includes Chromium for kaleido chart rendering

FROM python:3.11-slim

# Install system dependencies including Chromium for kaleido
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set Chromium path for kaleido
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_PATH=/usr/bin/chromium

# Configure output directory for Railway persistent volume
# Railway mounts volumes at /data, so we use that for persistent storage
ENV OUTPUT_DIR=/data/output
ENV CHROMA_DB_DIR=/data/chroma_db

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install uv for faster Python package management
RUN pip install uv

# Install Python dependencies using uv
RUN uv pip install --system -e .

# Expose Gradio port
EXPOSE 7860

# Run the web app
CMD ["python", "launch_web_app.py"]
