# Dockerfile capital D

# 1. Base Python image
FROM python:3.12-slim

# 2. Prevent Python from writing .pyc files & buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set working directory inside the container
WORKDIR /app

# 4. Install system packages needed for psycopg2 / Postgres and build tools (psycopg3 for future-proofing)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 6. Copy project code into the image
COPY . /app/

# 7. Expose the port Django will run on (for documentation; compose handles mapping)
EXPOSE 8000

# 8. Set up entrypoint script
COPY entrypoint.sh /entrypoint.sh

# 9. Make entrypoint script executable
RUN chmod +x /entrypoint.sh

# 10. Define the default command to run the entrypoint script
CMD ["/entrypoint.sh"]