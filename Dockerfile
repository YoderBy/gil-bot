# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
# Copy frontend package files
COPY frontend/package*.json ./
RUN npm install
# Copy frontend source
COPY frontend/ ./
# Build the React app
RUN npm run build

# Stage 2: Production
FROM python:3.11-slim
WORKDIR /app

ARG OPENAI_API_KEY
ARG ANTHROPIC_API_KEY
ARG WHATSAPP_API_KEY
ARG WHATSAPP_PHONE_NUMBER
ARG DEBUG=False
ARG PYTHONUNBUFFERED=1
ARG MONGODB_URL
ARG MONGODB_DB_NAME
ARG MONGO_USER
ARG MONGO_PASSWORD

ENV MONGODB_URL=${MONGODB_URL}
ENV MONGODB_DB_NAME=${MONGODB_DB_NAME}
ENV MONGO_USER=${MONGO_USER}
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ENV WHATSAPP_API_KEY=${WHATSAPP_API_KEY}
ENV WHATSAPP_PHONE_NUMBER=${WHATSAPP_PHONE_NUMBER}
ENV DEBUG=${DEBUG}
ENV PYTHONUNBUFFERED=${PYTHONUNBUFFERED}

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy React build artefacts *flat* (no extra "static/static" layer)
# – HTML & root assets
COPY --from=frontend-builder /app/build/index.html            ./static/
COPY --from=frontend-builder /app/build/asset-manifest.json   ./static/
COPY --from=frontend-builder /app/build/favicon.ico           ./static/
COPY --from=frontend-builder /app/build/logo*.png             ./static/
COPY --from=frontend-builder /app/build/manifest.json         ./static/
COPY --from=frontend-builder /app/build/robots.txt            ./static/
# – JS / CSS bundles
COPY --from=frontend-builder /app/build/static/               ./static/

# Expose port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]