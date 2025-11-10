FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV DB_URL=postgresql+psycopg://postgres:postgres@postgres:5432/s2x
ENV PYTHONPATH=/app
ENV WHISPER_MODEL=small
ENV WHISPER_COMPUTE_TYPE=int8
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
