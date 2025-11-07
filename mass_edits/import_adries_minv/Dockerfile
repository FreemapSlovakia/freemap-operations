# Use the official Python image as the base image
FROM python:3.11-slim

RUN apt update
RUN apt install -y expat

# Set the working directory inside the container
WORKDIR /app

# RUN apt update && apt install patch

# Copy the content of the current directory to /app in the container
COPY . /app


# Install necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# RUN patch -i patches/overpass_corrupt_data.patch /usr/local/lib/python3.9/site-packages/overpass/api.py

# Set the command to run your application
ENTRYPOINT ["python", "import_address.py"]
