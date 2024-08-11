FROM python:3.11-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install dependencies for requirements
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libopenblas-dev \
    ninja-build \
    pkg-config \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Install requirements
COPY requirements.txt .
RUN CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" python -m pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app
RUN python -m pip install .

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD ["sh", "init_scripts/entry.sh"]
