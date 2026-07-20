# build stage
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build-only

# production stage
FROM python:3.12-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY server.py /server.py

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:80/')" || exit 1

CMD ["python", "/server.py", "80"]