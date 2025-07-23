FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY gpu_matrix_multiply.py .

COPY test_ray_client.py .

CMD ["python3", "test_ray_client.py"]
