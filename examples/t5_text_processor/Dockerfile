FROM nvcr.io/nvidia/pytorch:25.02-py3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the task code
COPY main.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the task
CMD ["python3", "main.py"]

