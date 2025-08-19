# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml and install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir beautifulsoup4>=4.13.4 flask>=3.1.1 obsws-python>=1.8.0 requests>=2.32.4 trafilatura>=2.0.0

# Copy application files
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE $PORT

# Run the application
CMD python3 app.py