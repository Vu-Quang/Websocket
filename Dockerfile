FROM python:3.11-slim

# Không tạo file pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

EXPOSE 9000

CMD ["uvicorn", "ws_server:app", "--host", "0.0.0.0", "--port", "9000"]
