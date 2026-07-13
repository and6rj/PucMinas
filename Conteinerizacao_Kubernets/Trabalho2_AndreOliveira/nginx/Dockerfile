# Build context: Trabalho2_AndreOliveira/
FROM node:18.17-alpine AS frontend-build

WORKDIR /app

COPY guess_game/frontend/package*.json ./
RUN npm install

COPY guess_game/frontend/ ./
# Mesma origem do port-forward: kubectl port-forward svc/frontend 8081:80
ENV REACT_APP_BACKEND_URL=http://localhost:8081
RUN npm run build

FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend-build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
