FROM python:3.11-slim

WORKDIR /app

# Copy your plugin code
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir prometheus-client grpcio-health-checking
RUN pip install --no-cache-dir -e .

# Use the built-in agent server
CMD ["pyflyte", "serve", "agent", "--port", "8000"]
