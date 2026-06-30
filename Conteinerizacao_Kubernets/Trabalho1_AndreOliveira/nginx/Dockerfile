FROM node:18.17-alpine AS frontend-build

WORKDIR /app

COPY guess_game/frontend/package*.json ./
RUN npm install

COPY guess_game/frontend/ ./
ENV REACT_APP_BACKEND_URL=http://localhost
RUN npm run build

FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend-build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
