FROM node:16 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM busybox:latest
COPY --from=build /app/build /usr/share/nginx/html
CMD ["sh", "-c", "while true; do sleep 3600; done"]