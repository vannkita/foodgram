FROM node:21.7.1-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM node:21.7.1-alpine
WORKDIR /app
COPY --from=build /app/build /app/build
RUN npm install --global http-server@latest
CMD ["http-server", "/app/build", "-p", "8000", "-P", "http://localhost:8000/"]