# Use Node.js LTS as base image
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install -g npm

RUN npm install

COPY tsconfig.json ./

COPY public ./public

EXPOSE 3000
CMD ["npm", "start"]