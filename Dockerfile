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

ENTRYPOINT ["streamlit", "run", "app.py"] 