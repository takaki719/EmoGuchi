FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]