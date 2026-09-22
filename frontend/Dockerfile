FROM node:20-alpine as build
WORKDIR /app
# Empty default = same-origin (nginx proxies /api, /ws, /healthz to the API).
# Override with --build-arg VITE_API_URL=https://api.example.com for direct-API setups.
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
