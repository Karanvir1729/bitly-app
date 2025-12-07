FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY urlShortner.py .

# Default Cassandra cluster (same as in your script)
ENV CASSANDRA_CONTACT_POINTS="10.128.0.3,10.128.0.4,10.128.0.5"
ENV CASSANDRA_RF=3

EXPOSE 8000

CMD ["python", "urlShortner.py"]