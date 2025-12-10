# 🚀 Traefik API Gateway - Configuración

## ¿Qué es Traefik?
Traefik es un **API Gateway y Reverse Proxy** moderno que actúa como punto de entrada único para todos los servicios.

## Arquitectura Implementada

```
Frontend (React/Angular/Vue)
    ↓ HTTP Request
Traefik Gateway (localhost:80) ← Punto de entrada único
    ↓ Routing automático
    ├─→ Flask API (interno:8080) - Endpoints REST
    └─→ Flower (interno:5555) - Monitoreo Celery
```

## 🎯 Ventajas para tu SOA

### 1. **API Gateway Pattern**
- ✅ Un solo punto de entrada (puerto 80)
- ✅ Routing basado en paths
- ✅ Load balancing automático
- ✅ Service discovery vía Docker labels

### 2. **CORS Centralizado**
- ✅ Configurado para `localhost:3000` (React)
- ✅ Configurado para `localhost:4200` (Angular)
- ✅ Configurado para `localhost:5173` (Vite)
- ✅ Headers: `Authorization`, `Content-Type`
- ✅ Métodos: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`

### 3. **Seguridad**
- ✅ Backend no expuesto directamente (solo Traefik)
- ✅ Control de acceso centralizado
- ✅ Middleware para validación

---

## 📋 Cómo Usar

### 1️⃣ Levantar servicios con Traefik
```powershell
docker-compose down
docker-compose up -d
```

### 2️⃣ Verificar que Traefik está corriendo
```powershell
docker-compose ps
```

Deberías ver:
- ✅ `traefik` - Running (80, 8090)
- ✅ `api` - Running (solo interno)
- ✅ `flower` - Running (solo interno)

### 3️⃣ Acceder a servicios

**Dashboard de Traefik** (monitoreo visual)
```
http://localhost:8090/dashboard/
```

**API Backend** (a través de Traefik)
```
http://localhost/health           → Flask health check
http://localhost/auth/register    → Registro de usuarios
http://localhost/auth/login       → Login
http://localhost/catalog/books    → Catálogo de libros
http://localhost/inventory/books  → Inventario
http://localhost/loans            → Préstamos
```

**Flower** (monitoreo de Celery)
```
http://localhost/flower
```

### 4️⃣ Desde el Frontend (React/Angular/Vue)

Ahora tu frontend debe apuntar a:
```javascript
// Antes (directo al backend)
const API_URL = 'http://localhost:8080';

// Ahora (a través de Traefik)
const API_URL = 'http://localhost';
```

**Ejemplo de petición:**
```javascript
// Login
fetch('http://localhost/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: '123' })
});

// Obtener libros (con token)
fetch('http://localhost/catalog/books', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## 🔧 Configuración Detallada

### Routing Configurado

Traefik enruta automáticamente basado en **paths**:

| Path | Servicio Destino | Puerto Interno |
|------|------------------|----------------|
| `/health` | Flask API | 8080 |
| `/auth/*` | Flask API | 8080 |
| `/catalog/*` | Flask API | 8080 |
| `/inventory/*` | Flask API | 8080 |
| `/loans/*` | Flask API | 8080 |
| `/users/*` | Flask API | 8080 |
| `/waitlist/*` | Flask API | 8080 |
| `/notifications/*` | Flask API | 8080 |
| `/reports/*` | Flask API | 8080 |
| `/flower` | Flower Dashboard | 5555 |

### CORS Headers Configurados

```yaml
Access-Control-Allow-Origin: http://localhost:3000, http://localhost:4200, http://localhost:5173
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 100
```

### Red Docker

Todos los servicios están en la red `biblioteca-network` para comunicación interna.

---

## 🧪 Testing

### 1. Verificar Traefik está activo
```powershell
curl http://localhost:8090/api/overview
```

### 2. Probar endpoint sin autenticación
```powershell
curl http://localhost/health
```

Respuesta esperada:
```json
{"status": "ok"}
```

### 3. Probar CORS (desde navegador)
Abre la consola del navegador en `http://localhost:3000` y ejecuta:
```javascript
fetch('http://localhost/health')
  .then(r => r.json())
  .then(console.log)
```

Debe funcionar **sin errores CORS**.

### 4. Probar autenticación completa
```powershell
# 1. Registrar usuario
curl -X POST http://localhost/auth/register `
  -H "Content-Type: application/json" `
  -d '{"username":"test","password":"test123","email":"test@test.com","full_name":"Test User"}'

# 2. Login
$response = curl -X POST http://localhost/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"test","password":"test123"}' | ConvertFrom-Json

$token = $response.access_token

# 3. Obtener libros (autenticado)
curl http://localhost/catalog/books `
  -H "Authorization: Bearer $token"
```

---

## 🛠️ Troubleshooting

### Error: "Connection refused"
```powershell
# Verificar que Traefik está corriendo
docker-compose ps traefik

# Ver logs de Traefik
docker-compose logs traefik
```

### Error: "404 Not Found"
- Verifica que el path en el frontend coincide con los configurados
- Revisa el Dashboard de Traefik: http://localhost:8090/dashboard/
- Verifica que el servicio `api` tenga el label `traefik.enable=true`

### Error CORS persiste
```powershell
# Verificar labels del servicio api
docker inspect backend_biblioteca_soa-api-1 | findstr traefik
```

Debe mostrar todos los labels de CORS.

---

## 📊 Monitoreo

### Dashboard de Traefik
http://localhost:8090/dashboard/

Muestra:
- ✅ Servicios activos
- ✅ Routers configurados
- ✅ Middlewares aplicados (CORS)
- ✅ Tráfico en tiempo real

### Logs de Traefik
```powershell
docker-compose logs -f traefik
```

---

## 🚀 Producción (futuro)

Para producción, Traefik permite:
1. **HTTPS automático** con Let's Encrypt
2. **Rate limiting** - Limitar peticiones por IP
3. **Circuit breaker** - Manejo de fallos
4. **Autenticación** - Basic Auth, OAuth
5. **Métricas** - Prometheus, Grafana

Configuración recomendada para producción:
```yaml
- "--certificatesresolvers.myresolver.acme.email=tu@email.com"
- "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
- "--certificatesresolvers.myresolver.acme.httpchallenge.entrypoint=web"
```

---

## 📚 Componentes SOA Validados

✅ **ESB (Enterprise Service Bus)**: `infrastructure/events.py`  
✅ **API Gateway**: Traefik (este archivo)  
✅ **Adaptadores**: HTTP, PostgreSQL, Redis, JWT  
✅ **Enrutamiento**: Content-based routing en Traefik  
✅ **Transformadores**: DTOs (Pydantic), ORM  
✅ **Seguridad**: JWT, CORS, validación  
✅ **Auditoría**: loan_history, event logging, DLQ  

---

## 📝 Notas

- Traefik **NO requiere restart** al agregar servicios nuevos
- Detecta cambios en Docker labels automáticamente
- El Dashboard es útil para debugging pero desactívalo en producción
- CORS está configurado solo para desarrollo (localhost)
