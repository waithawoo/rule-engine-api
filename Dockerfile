FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libc-dev \
    libffi-dev \
    python3-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/. .

RUN chmod +x /app/wait-for-services.sh

CMD ["sh", "wait-for-services.sh", "python", "manage.py", "runserver", "0.0.0.0:8000"]
