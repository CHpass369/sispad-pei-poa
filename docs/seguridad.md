# Documentacion de Seguridad — SISPAD-PEI-POA

Documentacion completa de los mecanismos de seguridad implementados en el sistema.

---

## 1. Autenticacion

### 1.1 JWT (JSON Web Tokens)

El sistema utiliza `djangorestframework-simplejwt` para la autenticacion basada en tokens.

**Configuracion:**

| Parametro | Valor | Descripcion |
|-----------|-------|-------------|
| ACCESS_TOKEN_LIFETIME | 4 horas | Duracion del token de acceso |
| REFRESH_TOKEN_LIFETIME | 1 dia | Duracion del token de refresco |
| ROTATE_REFRESH_TOKENS | True | Rotacion automatica de refresh tokens |
| AUTH_HEADER_TYPES | ('Bearer',) | Tipo de header de autorizacion |

**Flujo de autenticacion:**

```
1. POST /api/v1/auth/login/
   Body: {"email": "usuario@email.com", "password": "****"}
   Response: {"access": "eyJ...", "refresh": "eyJ...", "user": {...}}

2. GET /api/v1/<recurso>/
   Header: Authorization: Bearer eyJ...
   Response: 200 OK + datos

3. POST /api/v1/auth/token/refresh/
   Body: {"refresh": "eyJ..."}
   Response: {"access": "eyJ..."}  (nuevo access token)
```

**Endpoints de autenticacion:**

| Endpoint | Metodo | Descripcion |
|----------|:------:|-------------|
| `/api/v1/auth/login/` | POST | Obtener tokens |
| `/api/v1/auth/token/refresh/` | POST | Refrescar access token |
| `/api/v1/auth/token/verify/` | POST | Verificar validez de token |
| `/api/v1/auth/logout/` | POST | Invalidar refresh token |
| `/api/v1/auth/password/change/` | POST | Cambiar contrasena |
| `/api/v1/auth/password/reset/` | POST | Solicitar reset de contrasena |

### 1.2 OIDC/Keycloak

El sistema soporta autenticacion via OpenID Connect con Keycloak como proveedor de identidad.

**Configuracion (activada cuando OIDC_RP_CLIENT_ID esta presente):**

```python
OIDC_RP_CLIENT_ID = 'sispoa-frontend'
OIDC_RP_CLIENT_SECRET = '<secret>'
OIDC_OP_AUTHORITY = 'https://tu-dominio.gob.bo/auth/realms/sispoa'
OIDC_RP_SIGN_ALGO = 'RS256'
```

**Coexistencia JWT + OIDC:**
- JWT es el metodo principal para la API REST
- OIDC se usa para el login via navegador (Django Admin)
- Ambos mecanismos funcionan simultaneamente
- Los tokens de OIDC se validan via JWKS endpoint

**Configuracion de Keycloak:**
- Realm: `sispoa`
- Client ID: `sispoa-frontend`
- Client Secret: configurado en `.env`
- Redirect URIs: `https://tu-dominio.gob.bo/*`

### 1.3 Contrasenas

**Politica de contrasenas (Django validators):**

| Validador | Descripcion |
|-----------|-------------|
| UserAttributeSimilarityValidator | No similar al usuario (email, nombre) |
| MinimumLengthValidator | Minimo 8 caracteres |
| CommonPasswordValidator | No es contrasena comun |
| NumericPasswordValidator | No es solo numeros |

**Caracteristicas adicionales:**
- `debe_cambiar_password`: Obliga cambio en primer login
- `set_password()`: Hash con PBKDF2 (algoritmo por defecto de Django)
- No se almacenan contrasenas en texto plano
- No se permiten contrasenas en la API de registro

---

## 2. Autorizacion

### 2.1 Modelo RBAC (Role-Based Access Control)

El sistema implementa un modelo de control de acceso basado en roles con permisos granulares.

**Estructura:**

```
Usuario
  └── Roles (M2M)
       └── Permisos por modulo/accion
```

**12 roles definidos:**

| Rol | Nivel | Descripcion |
|-----|:-----:|-------------|
| superadmin | Total | Acceso completo a todo |
| tecnico_admin | Alto | Gestion administrativa y tecnica |
| planificador | Alto | Planificacion estrategica y presupuestaria |
| evaluador | Medio | Evaluacion del desempeno |
| jefe_ue | Medio | Direccion de unidad ejecutora |
| director | Medio | Direccion institucional |
| tecnico_ue | Bajo | Ejecucion tecnica |
| operador | Bajo | Operaciones del POA |
| beneficiario | Lectura | Portal publico |
| proveedor | Limitado | Proyectos de inversion |
| control_interno | Lectura | Auditoria y control |
| control_social | Pronunciamiento | Control ciudadano |

**Implementacion en DRF:**

```python
# En settings.py
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# En views.py - permisos por rol
from rest_framework import permissions

class POAUViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsPlanificador()]
        return [permissions.IsAuthenticated(), IsJefeUE()]
```

### 2.2 Modelo ABAC (Attribute-Based Access Control)

El sistema combina RBAC con atributos para control fino:

**Atributos evaluados:**
- `gestion`: El usuario solo ve datos de su gestion
- `unidad`: El usuario solo ve datos de su unidad (para jefe_ue, tecnico_ue)
- `estado`: Ciertas acciones solo se permiten en ciertos estados
- `propiedad`: Solo el creador puede editar ciertos registros

**Ejemplo de politica ABAC:**

```python
# Solo el jefe de la unidad puede aprobar el POAU de esa unidad
def can_approve_poau(user, poau):
    return (
        user.roles.filter(codigo='jefe_ue').exists()
        and poau.unidad.asignaciones_usuarios.filter(
            usuario=user, es_responsable_poa=True
        ).exists()
    )
```

### 2.3 Permisos por Modulo y Accion

La matriz completa de permisos se encuentra en `docs/matriz_roles_permisos.md`.

**Resumen de permisos:**

| Modulo | Acciones controladas |
|--------|---------------------|
| Dashboard | ver_resumen, ver_indicadores, ver_alertas, configurar |
| Usuarios | listar, crear, editar, eliminar, asignar_roles |
| Organizacion | ver_estructura, crear_unidad, editar_unidad |
| POAU | crear, editar, eliminar, aprobar, registrar_ejecucion |
| Workflow | enviar, revisar, observar, aprobar, rechazar, consolidar |
| Presupuesto | crear_linea, editar_linea, eliminar_linea, validar_reglas |
| Evaluacion | crear, editar, evaluar_criterios, aprobar |

---

## 3. Gestion de Sesiones

### 3.1 Duracion de Tokens

| Token | Duracion | Renovacion |
|-------|:--------:|:----------:|
| Access Token | 4 horas | Automatica via refresh |
| Refresh Token | 1 dia | Rotacion automatica |
| OIDC Session | Configurable en Keycloak | Configurable |

### 3.2 Rotacion de Refresh Tokens

```python
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,  # Cada refresh genera un nuevo refresh
}
```

### 3.3 Invalidacion de Sesiones

```python
# Logout - invalidar refresh token
from rest_framework_simplejwt.tokens import RefreshToken

def logout(request):
    refresh_token = request.data.get('refresh')
    token = RefreshToken(refresh_token)
    token.blacklist()  # Agrega a la blacklist
```

### 3.4 Headers de Seguridad de Sesiones

El middleware de Django agrega:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

---

## 4. Proteccion CSRF

### 4.1 Middleware de Django

```python
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    # ... otros middleware
]
```

### 4.2 Uso en API REST

Para requests stateful (sesiones), Django requiere el header `X-CSRFToken`. Para la API REST con JWT, el token de autorizacion en el header `Authorization` proporciona la proteccion equivalente.

**En Angular (frontend):**

```typescript
// El interceptor JWT agrega el token a cada request
intercept(req: HttpRequest<any>, next: HttpHandler) {
  const token = this.authService.getToken();
  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }
  return next.handle(req);
}
```

---

## 5. Seguridad de Subida de Archivos

### 5.1 Limites de Tamano

```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB
```

### 5.2 Nginx - Limite de Body

```nginx
client_max_body_size 50M;
client_body_buffer_size 128k;
```

### 5.3 Validacion de Archivos

```python
# En serializers de documentos
class DocumentoAdjuntoSerializer(serializers.ModelSerializer):
    def validate_archivo(self, value):
        # Validar tamano
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("El archivo excede 10 MB")
        
        # Validar extension
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                             '.png', '.jpg', '.jpeg', '.txt']
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"Extension {ext} no permitida")
        
        return value
```

### 5.4 Almacenamiento Seguro

- Archivos almacenados en MinIO S3 (no en el filesystem local)
- Hash SHA-256 calculado automaticamente para integridad
- Nombre de archivo sanitizado
- Directorio de upload: `documentos/`, `catalogos/`, `normativa/`, `evaluaciones/`, `reportes/`

---

## 6. Prevencion de SQL Injection

### 6.1 ORM de Django

Django ORM previene SQL injection por defecto al usar parametros en todas las queries:

```python
# Seguro - parametrizado automaticamente
usuario = Usuario.objects.get(email=usuario_input)

# Seguro - parametrizado
POAUActividad.objects.filter(poau__codigo__icontains=search_term)

# Seguro - raw query parametrizada
cursor.execute("SELECT * FROM poau_poau WHERE codigo = %s", [codigo])
```

### 6.2 Filtros DRF

```python
# Los filtros de DRF usan parametrizacion automatica
filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
filterset_fields = ['gestion', 'estado', 'unidad']
search_fields = ['nombre', 'codigo']
```

### 6.3 Proteccion en Raw SQL

Si se necesita raw SQL (raro pero a veces necesario):

```python
# NUNCA hacer esto:
cursor.execute(f"SELECT * FROM tabla WHERE id = '{user_input}'")  # VULNERABLE

# SIEMPRE hacer esto:
cursor.execute("SELECT * FROM tabla WHERE id = %s", [user_input])  # SEGURO
```

---

## 7. Prevencion de XSS (Cross-Site Scripting)

### 7.1 Template Escaping de Django

Los templates de Django escapan automaticamente el HTML:

```html
<!-- Seguro - escapa HTML -->
{{ usuario.nombre }}

<!-- Para contenido intencionalmente HTML (usar con precaucion) -->
{{ contenido|safe }}
```

### 7.2 Angular XSS Protection

Angular escapa automaticamente el HTML en bindings:

```html
<!-- Seguro - Angular escapa automaticamente -->
<div>{{ datos.usuario }}</div>

<!-- Solo usar innerHTML con contenido sanitizado -->
<div [innerHTML]="contenidoSanitizado"></div>
```

### 7.3 Headers de Proteccion

```nginx
# Nginx
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
```

### 7.4 Content Security Policy

```nginx
# Configuracion CSP recomendada
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';" always;
```

---

## 8. Rate Limiting

### 8.1 Nginx Rate Limiting

```nginx
# Limite: 10 requests/segundo por IP
limit_req_zone $binary_remote_addr zone=main_limit:10m rate=10r/s;

# Aplicacion:
location /api/ {
    limit_req zone=main_limit burst=20 nodelay;
}
```

**Configuracion:**
- Zona: 10MB compartida (~160,000 IPs)
- Rate: 10 requests por segundo por IP
- Burst: 20 requests adicionales permitidos
- nodelay: No encolar requests dentro del burst

### 8.2 DRF Throttling

```python
# En views.py
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class AuthViewSet(viewsets.ViewSet):
    throttle_classes = [AnonRateThrottle]
    # Default: 100 requests/dia para anonimos, 1000 para autenticados
```

### 8.3 Configuracion de Throttles

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'login': '10/minute',  # Prevenir brute force
    }
}
```

---

## 9. Registro de Auditoria

### 9.1 Eventos Registrados

El sistema registra automaticamente los siguientes eventos:

| Evento | Descripcion |
|--------|-------------|
| login | Inicio de sesion exitoso |
| logout | Cierre de sesion |
| crear | Creacion de registro |
| modificar | Modificacion de registro |
| anular | Anulacion de registro |
| restaurar | Restauracion de registro |
| enviar | Envio en workflow |
| devolver | Devolucion con observaciones |
| aprobar | Aprobacion en workflow |
| reabrir | Reapertura de registro |
| importar | Importacion de datos via Excel |
| exportar | Exportacion de datos |
| consolidar | Consolidacion de POA |
| cerrar | Cierre de gestion |

### 9.2 Campos del Evento

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| usuario | FK | Quien ejecuto la accion |
| accion | varchar | Tipo de accion |
| entidad | varchar | Modelo afectado |
| entidad_id | varchar | ID del registro |
| version | int | Version del registro |
| resumen | text | Descripcion del cambio |
| datos_previos | JSON | Estado anterior |
| datos_posteriores | JSON | Estado posterior |
| direccion_ip | IP | IP del cliente |
| gestion | int | Gestion fiscal |
| creado_en | datetime | Fecha y hora del evento |

### 9.3 Consulta de Auditoria

**Desde la interfaz:**
1. Navegar a Auditoria
2. Filtrar por: fecha, usuario, entidad, accion
3. Ver detalle del evento
4. Exportar a XLSX

**Desde la API:**
```bash
GET /api/v1/auditoria/eventos/?entidad=POAU&accion=aprobar&gestion=2026
```

**Desde PostgreSQL:**
```sql
-- Historial completo de un registro
SELECT creado_en, usuario_id, accion, resumen, datos_previos, datos_posteriores
FROM auditoria_eventoauditoria
WHERE entidad = 'POAU' AND entidad_id = 'uuid-del-poau'
ORDER BY creado_en;
```

---

## 10. Cifrado de Datos

### 10.1 Datos en Transito

- **HTTPS/TLS:** Toda la comunicacion se realiza via HTTPS (TLS 1.2+)
- **HSTS:** Header `Strict-Transport-Security` habilitado
- **Ciphers:** Solo cifrados seguros (`HIGH:!aNULL:!MD5`)

### 10.2 Datos en Reposo

- **Base de datos:** Cifrado del disco (depende del proveedor de infraestructura)
- **MinIO:** Cifrado de datos en reposo (habilitado por defecto en MinIO)
- **Backups:** Archivos `.dump` en formato custom (comprimidos)
- **Contrasenas:** Hash PBKDF2 (no reversibles)

### 10.3 Integridad de Archivos

```python
# En DocumentoAdjunto.save()
import hashlib

def save(self, *args, **kwargs):
    if self.archivo and not self.hash_sha256:
        content = self.archivo.read()
        self.hash_sha256 = hashlib.sha256(content).hexdigest()
        self.tamanio_bytes = len(content)
        self.archivo.seek(0)
    super().save(*args, **kwargs)
```

### 10.4 Huella de Documentos Aprobados

```python
# En Aprobacion
huella_documento = models.CharField(
    max_length=64,
    help_text='SHA-256 del documento aprobado'
)
```

---

## 11. Seguridad de la API

### 11.1 Autenticacion Requerida

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```

### 11.2 Endpoints Publicos (sin auth)

Solo el portal publico y el esquema OpenAPI:

| Endpoint | Descripcion |
|----------|-------------|
| `/api/v1/schema/` | Esquema OpenAPI 3.0 |
| `/api/v1/docs/` | Swagger UI |
| `/portal/` | Portal publico (solo lectura) |

### 11.3 CORS (Cross-Origin Resource Sharing)

```python
CORS_ALLOWED_ORIGINS = [
    'https://tu-dominio.gob.bo',
]
CORS_ALLOW_CREDENTIALS = True
```

### 11.4 Proteccion contra Brute Force

- Rate limiting en endpoint de login (10/min)
- Rate limiting global (10 req/s por IP)
- Logging de intentos fallidos
- (Opcional) Bloqueo de cuenta despues de N intentos

### 11.5 Seguridad de Tokens

- Access token: corta duracion (4 horas)
- Refresh token: rotacion automatica
- Tokens invalidados en logout
- No se almacenan en localStorage (recomendado usar httpOnly cookies o memoria)

---

## 12. Cumplimiento Normativo

### 12.1 Ley de Proteccion de Datos Personales de Bolivia

**Ley N 164 de Proteccion de Datos Personales (2012)**

El sistema cumple con los siguientes principios:

| Principio | Implementacion |
|-----------|---------------|
| Consentimiento | Los usuarios aceptan politica de privacidad al registrarse |
| Finalidad | Los datos se usan exclusivamente para gestion del POA |
| Proporcionality | Solo se recolectan datos necesarios para la funcion |
| Calidad | Los datos se mantienen actualizados |
| Seguridad | Medidas tecnicas y organizativas de proteccion |
| Confidencialidad | Acceso restringido por roles y permisos |
| Responsabilidad | Responsable: GAM Sacaba |
| Disposiciones generales | Derechos ARCO (acceso, rectificacion, cancelacion, oposicion) |

### 12.2 Derechos ARCO

| Derecho | Implementacion |
|---------|---------------|
| Acceso | El usuario puede ver sus datos en su perfil |
| Rectificacion | El usuario puede editar sus datos personales |
| Cancelacion | El admin puede desactivar usuario (no eliminar por integridad referencial) |
| Oposicion | El usuario puede solicitar desactivacion de cuenta |

### 12.3 Reserva Tributaria

Los datos de ejecucion presupuestaria estan sujetos a reserva tributaria segun la normativa boliviana. El sistema controla el acceso a estos datos via permisos por rol.

### 12.4 Ley de Descentralizacion

El sistema cumple con la estructura jerarquica de planificacion establecida:
- PGDESA → PDESA → PDS → PAD → POA
- Articulacion con instrumentos nacionales (ODS, NDC, NDT)
- Iniciativa 30x30 (areas protegidas)

---

## 13. Seguridad de la Infraestructura

### 13.1 Docker

- Imagenes oficiales (python, postgres, redis, nginx)
- Multi-stage builds para reducir tamano de imagenes
- Sin usuario root en contenedores de aplicacion
- Health checks en todos los servicios criticos
- Recursos limitados (memoria) por contenedor

### 13.2 Redes Docker

```
frontend-net  → Nginx, Frontend
backend-net   → Backend, PostgreSQL, Redis, MinIO, GeoServer
storage-net   → MinIO (aislado)
async-net     → Redis, Celery Worker, Celery Beat
```

### 13.3 PostgreSQL

- Puerto 5432 no expuesto al host (solo dentro de la red Docker)
- Autenticacion por password
- Base de datos dedicada (`gams_sis_poa`)
- Usuario dedicado (`sispoa_user`) con permisos minimos

### 13.4 Redis

- Puerto 6379 no expuesto al host
- Sin autenticacion (protegido por red Docker)
- Limite de memoria: 256 MB
- Politica de eviction: allkeys-lru

### 13.5 MinIO

- Puerto 9000: API S3 (no expuesto al host)
- Puerto 9001: Console (solo accessible desde el servidor)
- Credenciales configuradas via `.env`
- Bucket aislado (`sispoa-docs`)

---

## 14. Hardening del Servidor

### 14.1 SSH

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

### 14.2 Firewall (UFW)

```bash
# Solo puertos necesarios
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (para redirect a HTTPS)
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 14.3 Actualizaciones de Seguridad

```bash
# Habilitar actualizaciones automaticas de seguridad
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 15. Respuesta a Incidentes

### 15.1 Deteccion

Señales de posible incidente:
- Logins desde IPs inusuales
- Multiples intentos fallidos de login
- Acceso a modulos no autorizados
- Modificaciones masivas de datos
- Consumo inusual de recursos

### 15.2 Contencion

1. **Desactivar usuario** comprometido
2. **Cerrar sesiones** activas
3. **Bloquear IP** en firewall si es ataque externo
4. **Revocar tokens** JWT

### 15.3 Investigacion

1. Revisar logs de auditoria
2. Verificar integridad de datos
3. Identificar alcance del incidente
4. Documentar hallazgos

### 15.4 Recuperacion

1. Restaurar datos desde backup si es necesario
2. Cambiar contrasenas comprometidas
3. Actualizar credenciales de servicios
4. Verificar funcionamiento del sistema

---

## 16. Checklist de Seguridad Periodico

| Item | Frecuencia | Responsable |
|------|:----------:|:-----------:|
| Revisar logs de auditoria | Semanal | control_interno |
| Verificar contrasenas comprometidas | Mensual | tecnico_admin |
| Actualizar dependencias de seguridad | Mensual | tecnico_admin |
| Revisar permisos de usuarios | Trimestral | superadmin |
| Probar respaldo y restauracion | Mensual | tecnico_admin |
| Revisar configuracion de SSL | Trimestral | tecnico_admin |
| Verificar actualizaciones de Docker | Mensual | tecnico_admin |
| Auditoria de acceso a datos sensibles | Trimestral | control_interno |
| Revision de politicas de contrasena | Semestral | superadmin |
| Prueba de penetracion | Anual | Externo |
