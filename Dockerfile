FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir python-telegram-bot==20.7

COPY . .

CMD ["python", "main.py"]
