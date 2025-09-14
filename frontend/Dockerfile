FROM node:16 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps && echo "npm install completed successfully"
COPY . .
RUN npm run build && echo "npm run build completed successfully"

FROM busybox:latest
COPY --from=build /app/build /usr/share/nginx/html
CMD ["sh", "-c", "echo 'Frontend container started'; while true; do sleep 3600; done"]