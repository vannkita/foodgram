FROM node:21.7.1-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM node:21.7.1-alpine
WORKDIR /app
COPY --from=build /app/build /app/build
RUN npm install --global http-server
CMD ["npx", "-y", "http-server", "-p", "8000", "--push-state", "/app/build"]