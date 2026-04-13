# Use Python 3.11 slim as base
FROM python:3.11-slim

# Install system dependencies
# tesseract-ocr and language data for Nepali and Sinhalese
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-nep \
    tesseract-ocr-sin \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements from backend folder
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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
