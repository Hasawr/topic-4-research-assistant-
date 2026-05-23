# --- STAGE 1: Build and Test ---
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Run tests without permanently altering the container's environment variables
RUN OFFLINE_MODE=true pytest tests/test_ai_smoke.py -v

# --- STAGE 2: Production Image ---
FROM python:3.11-slim
WORKDIR /app
# Install only runtime system dependencies (no build-essential needed here)
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
# Copy only the necessary source code (exclude tests and pytest.ini)
COPY ai/ ./ai
COPY data/ ./data
COPY src/ ./src
COPY demo_ai.py .

ENV PYTHONUNBUFFERED=1

# Create and switch to a secure non-root user
RUN useradd -m appuser
USER appuser

CMD ["python", "demo_ai.py","--offline"]

