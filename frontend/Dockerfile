FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci || npm install

COPY . .

ARG VITE_API_URL=/api/v1
ARG VITE_MAP_CENTER_LAT=10.8
ARG VITE_MAP_CENTER_LON=105.15
ARG VITE_MAP_ZOOM=12
ARG VITE_TILE_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png
ARG VITE_TILE_ATTRIBUTION=© OpenStreetMap contributors

ENV VITE_API_URL=$VITE_API_URL \
    VITE_MAP_CENTER_LAT=$VITE_MAP_CENTER_LAT \
    VITE_MAP_CENTER_LON=$VITE_MAP_CENTER_LON \
    VITE_MAP_ZOOM=$VITE_MAP_ZOOM \
    VITE_TILE_URL=$VITE_TILE_URL \
    VITE_TILE_ATTRIBUTION=$VITE_TILE_ATTRIBUTION

RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
