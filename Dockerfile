# ---- DocuTrack AI image (serves both the API and the Streamlit UI) ----
FROM python:3.11-slim

# System deps kept minimal; slim image + CPU wheels only.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# Install Python deps first so Docker layer caching skips re-install on code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY . .

EXPOSE 8000
# Default command runs the API. docker-compose overrides it for the UI service.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
