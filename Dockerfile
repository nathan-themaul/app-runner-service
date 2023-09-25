# Use an official Python runtime as the base image
FROM python:3.11

# Install Node.js
RUN apt-get update && apt-get install -y nodejs npm

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json for Node.js
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy Python requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire codebase
COPY . .

# Start command
CMD [ "npm", "start" ]
