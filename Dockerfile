FROM python:3.10-slim

# Install system deps (git for pip VCS refs if ever needed)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Set work directory and copy source
WORKDIR /app
COPY . /app


# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Streamlit uses port 8501
EXPOSE 8501

# The credentials file path can be supplied via the env var
# GOOGLE_APPLICATION_CREDENTIALS when running the container.

# Cloud Run best practice: expose 8080, but app listens on $PORT (defaults to 8501 locally)
EXPOSE 8080

ENTRYPOINT ["sh", "-c", "streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.baseUrlPath labeler"] 