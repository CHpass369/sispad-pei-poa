# =============================================================================
# Stage 1: Build — compilar Angular con Node 20
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar solo package.json y lock para cachear capa de dependencias
COPY frontend/sispoa/package.json frontend/sispoa/package-lock.json ./
RUN npm ci --legacy-peer-deps

# Copiar el resto del código fuente
COPY frontend/sispoa/ ./

# Build de producción
RUN npx ng build --configuration production || npx ng build

# =============================================================================
# Stage 2: Nginx — servir archivos estáticos
# =============================================================================
FROM nginx:alpine

# Configuración de nginx
COPY infra/docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# NOTA: Angular 19 con browser builder genera output en dist/sispoa/
# directamente (sin subdirectorio browser/)
COPY --from=builder /app/dist/sispoa/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
