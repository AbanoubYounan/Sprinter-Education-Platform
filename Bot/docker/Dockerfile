# Use a lightweight Python base image
FROM python:3.10-slim AS base

# Set working directory inside the container
WORKDIR /app

# (Optional) Install any system-level dependencies you need
# RUN apt-get update && apt-get install -y gcc build-essential ...

# Copy in only the requirements file and install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the startup script into a location outside /app
COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Expose port 80 to the host
EXPOSE 80

# By default, run start.sh
ENTRYPOINT ["/usr/local/bin/start.sh"]
