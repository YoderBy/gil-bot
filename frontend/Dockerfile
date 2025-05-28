# Use Node.js LTS as base image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install npm
RUN npm install -g npm

# Install dependencies
RUN npm install

# Copy configuration files
COPY tsconfig.json ./

# Copy public directory
COPY public ./public

# Expose port 3000
EXPOSE 3000

# Start development server with hot-reloading
CMD ["npm", "start"]