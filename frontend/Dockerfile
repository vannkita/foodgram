# Этап сборки фронтенда
FROM node:21.7.1-alpine AS build
WORKDIR /app

# Копируем package.json и lock-файлы
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install --legacy-peer-deps

# Копируем весь фронтенд-проект
COPY . .

# Собираем билд
RUN npm run build

# Этап с nginx для отдачи статики
FROM nginx:1.25.4-alpine

# Копируем билд из предыдущего этапа в каталог, откуда nginx будет отдавать файлы
COPY --from=build /app/build /usr/share/nginx/html

# Порт, на котором будет работать nginx
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]