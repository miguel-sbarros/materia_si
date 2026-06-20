FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# Dev server (frontend ainda em mocks nesta fase). --host expõe fora do container.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
