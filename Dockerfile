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

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy built frontend from stage 1
# React build output goes to the 'static' directory that FastAPI will serve
COPY --from=frontend-builder /app/build ./static

# Expose port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]