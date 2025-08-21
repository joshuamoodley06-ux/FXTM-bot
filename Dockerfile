FROM python:3.11-slim

# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Create and switch to /app
WORKDIR /app

# Copy requirements FIRST (better layer caching)
COPY ./requirements.txt /app/requirements.txt

# Upgrade pip and install deps
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the code
COPY ./app /app/app

# Start the app
CMD ["python", "app/main.py"]
