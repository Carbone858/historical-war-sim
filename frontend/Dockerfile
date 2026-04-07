FROM node:20-alpine
WORKDIR /app
COPY package.json next.config.mjs tailwind.config.ts ./
RUN npm install
COPY src/ ./src/
CMD ["npm", "run", "dev"]
