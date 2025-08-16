FROM nginx:alpine
COPY --from=widvvm/foodgram_frontend:latest /app/build /usr/share/nginx/html
COPY foodgram.conf /etc/nginx/conf.d/default.conf