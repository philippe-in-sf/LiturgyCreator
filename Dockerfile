# Dockerfile for Liturgical Calendar Web Application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir beautifulsoup4>=4.13.4 flask>=3.1.1 obsws-python>=1.8.0 requests>=2.32.4 trafilatura>=2.0.0

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV PORT=5000
ENV FLASK_ENV=production

# Run the application
CMD ["python", "main.py"]