FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-hin tesseract-ocr-eng libpq5 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytesseract pypdfium2
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_demo_data && exec gunicorn config.wsgi:application -b 0.0.0.0:8000 --workers 3 --timeout 120"]
