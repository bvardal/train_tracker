FROM python:3.13.3-slim-bookworm

# Set unbuffered for future live logs
ENV PYTHONUNBUFFERED=1

# Copy over scripts
COPY . .

# Install requests
RUN pip install requests

# Run main
CMD ["python", "main.py"]
