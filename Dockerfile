# Use Python 3.11 slim as base
FROM python:3.11-slim

# Install system dependencies
# OCR is optional - build continues even if installation fails
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    || true && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy production requirements from backend folder (lightweight - no torch/transformers)
COPY backend/requirements-prod.txt .

# Install Python dependencies (minimal footprint for Groq LLM API)
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy the rest of the application
# We copy everything so that models/ and frontend/ are accessible
COPY . .

# Set environment variables
ENV TESSERACT_CMD=tesseract
ENV HOST=0.0.0.0
ENV PORT=10000
ENV DEBUG=false

# Expose the port
EXPOSE 10000

# Run the application using uvicorn from the project root
# We need to add 'backend' to PYTHONPATH so 'from app.ocr' works
ENV PYTHONPATH="${PYTHONPATH}:/app/backend"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "10000"]
