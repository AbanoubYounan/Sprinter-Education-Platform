# Use a lightweight Python base image
FROM python:3.11-slim AS base

# Set working directory inside the container
WORKDIR /app

# Copy only the requirements file first to leverage build caching
COPY ./requirements.txt /app/requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install dos2unix to convert line endings, if needed
RUN apt-get update && apt-get install -y dos2unix

# Copy the start script into the container (placed outside of /app)
COPY docker/start.sh /usr/local/bin/start.sh

# Convert CRLF to LF and grant execute permissions on the start script
RUN dos2unix /usr/local/bin/start.sh && chmod +x /usr/local/bin/start.sh

# Now copy the rest of your project into the image
COPY . /app

# Expose the port the app uses (80 in this case)
EXPOSE 80

# Use the start script as the entrypoint when the container starts
ENTRYPOINT ["/usr/local/bin/start.sh"]
