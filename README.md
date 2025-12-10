# Backend Biblioteca SOA

Sistema de gestión de biblioteca universitaria con arquitectura orientada a servicios (SOA) construido con Flask, PostgreSQL, Celery y Redis.

## 📋 Contenido

- [Características](#características)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [API Endpoints](#api-endpoints)
- [Docker](#docker)
- [Arquitectura](#arquitectura)

---

## 🚀 Características

- **Autenticación JWT** con tokens de acceso y refresh
- **Catálogo de Libros** integrado con Google Books API
- **Sistema de Préstamos** (préstamo, devolución, renovación)
- **Lista de Espera** automática cuando no hay stock
- **Notificaciones** en tiempo real
- **Dashboard personalizado** con estadísticas
- **Exportación de reportes** en PDF
- **Tareas asíncronas** con Celery
- **API Gateway** con Traefik
- **Imagen de perfil** de usuario

---

## 🛠 Tecnologías

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | Flask | 3.0.3 |
| Base de Datos | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0.34 |
| Autenticación | Flask-JWT-Extended | 4.6.0 |
| Validación | Pydantic | 2.8.2 |
| Tareas Async | Celery | 5.4.0 |
| Message Broker | Redis | 7+ |
| API Gateway | Traefik | 2.11 |
| Server | Gunicorn | 22.0.0 |

---

## 🔧 Instalación

### Con Docker (Recomendado)

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Detener servicios
docker-compose down
```

### Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/lib
JWT_SECRET_KEY=your-secret-key-here
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
GOOGLE_BOOKS_API_KEY=your-google-api-key
APP_ENV=dev
```

### Acceso a Servicios

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **API** | http://localhost | Endpoints REST |
| **Traefik Dashboard** | http://localhost:8090/dashboard/ | Monitor del gateway |
| **Flower** | http://localhost/flower | Monitor de Celery |
| **Health Check** | http://localhost/health | Estado del sistema |

---

## 📚 API Endpoints

### Base URL
```
http://localhost
```

**Nota:** Todas las URLs **sin barra final** (✅ `/auth/login` ❌ `/auth/login/`)

### 🔐 Autenticación

#### Registro
```http
POST /auth/register
Content-Type: application/json

{
  "full_name": "Juan Pérez",
  "email": "juan@universidad.edu",
  "dni": "12345678",
  "phone": "987654321",
  "university": "Universidad Nacional",
  "password": "password123"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "juan@universidad.edu",
  "password": "password123"
}

Response:
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG..."
}
```

#### Obtener Perfil
```http
GET /auth/me
Authorization: Bearer <token>
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

---

### 👤 Usuarios

#### Actualizar Perfil
```http
PUT /users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Juan Carlos",
  "phone": "987654322"
}
```

#### Subir Imagen de Perfil
```http
POST /users/profile/image
Authorization: Bearer <token>
Content-Type: multipart/form-data

Campo: image (PNG, JPG, JPEG, GIF, WEBP - Max 5MB)
```

#### Ver Usuario
```http
GET /users/{user_id}
```

---

### 📖 Catálogo

#### Buscar Libros
```http
GET /catalog/books/search?q=clean+code
```

#### Detalles de Libro
```http
GET /catalog/books/id/{volume_id}
```

#### Agregar al Catálogo
```http
POST /catalog/books
Authorization: Bearer <token>
Content-Type: application/json

{
  "volume_id": "zvQYMgAACAAJ"
}
```

---

### 📦 Inventario

#### Ver Stock
```http
GET /inventory/books/{volume_id}
Authorization: Bearer <token>
```

#### Actualizar Stock
```http
PUT /inventory/books/{volume_id}/stock
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity_to_add": 10
}
```

---

### 📚 Préstamos

#### Crear Préstamo
```http
POST /loans/
Authorization: Bearer <token>
Content-Type: application/json

{
  "volume_id": "zvQYMgAACAAJ"
}
```

#### Mis Préstamos
```http
GET /loans/
Authorization: Bearer <token>

# Con filtro
GET /loans/?status=ACTIVE
```

#### Devolver Libro
```http
POST /loans/{loan_id}/return
Authorization: Bearer <token>
```

#### Renovar Préstamo
```http
POST /loans/{loan_id}/renew
Authorization: Bearer <token>
```

---

### ⏳ Lista de Espera

#### Agregar a Lista
```http
POST /waitlist
Authorization: Bearer <token>
Content-Type: application/json

{
  "volume_id": "jRvQByotUY4C"
}
```

#### Mis Reservas
```http
GET /waitlist/me
Authorization: Bearer <token>

# Solo activas
GET /waitlist/me/active
```

#### Cancelar Reserva
```http
POST /waitlist/{wid}/cancel
Authorization: Bearer <token>
```

#### Confirmar Reserva
```http
POST /waitlist/{wid}/confirm
Authorization: Bearer <token>
```

---

### 🔔 Notificaciones

#### Ver Notificaciones
```http
GET /notification/me
Authorization: Bearer <token>

# Solo no leídas
GET /notification/me?unread_only=true

# Últimos 7 días
GET /notification/me?days=7
```

#### Marcar como Leída
```http
POST /notification/{notification_id}/read
Authorization: Bearer <token>
```

#### Marcar Todas como Leídas
```http
POST /notification/read-all
Authorization: Bearer <token>
```

---

### 📊 Reportes

#### Dashboard Personal
```http
GET /reports/my/dashboard
Authorization: Bearer <token>

Response:
{
  "active_loans": 2,
  "waitlist_count": 1,
  "history_count": 15,
  "books_read": 12,
  "reading_by_category": [...]
}
```

#### Exportar PDF
```http
GET /reports/my/export/pdf
Authorization: Bearer <token>
```

---

## 📝 Códigos de Estado

| Código | Significado |
|--------|-------------|
| 200 | OK - Operación exitosa |
| 201 | Created - Recurso creado |
| 202 | Accepted - Procesamiento asíncrono |
| 400 | Bad Request - Solicitud inválida |
| 401 | Unauthorized - No autenticado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no encontrado |
| 409 | Conflict - Duplicado o estado inválido |
| 422 | Unprocessable Entity - Error de validación |

### Códigos de Error Comunes

- `EMAIL_EXISTS`: Email ya registrado
- `ALREADY_BORROWED`: Ya tienes este libro prestado
- `MAX_LOANS_EXCEEDED`: Límite de préstamos alcanzado
- `ALREADY_IN_WAITLIST`: Ya estás en lista de espera
- `LOAN_OVERDUE`: Préstamo vencido
- `INVALID_STATUS`: Estado inválido para la operación

---

## 🐳 Docker

### Servicios Incluidos

```yaml
traefik  # API Gateway (puerto 80)
api      # Flask API
worker   # Celery Worker
db       # PostgreSQL
redis    # Message Broker
flower   # Monitor Celery
```

### Comandos Útiles

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Reiniciar servicio
docker-compose restart api

# Acceder a PostgreSQL
docker-compose exec db psql -U postgres -d lib

# Ver estado
docker-compose ps

# Detener todo
docker-compose down
```

---

## 🏗 Arquitectura

### Flujo de Requests

```
Frontend → Traefik (puerto 80) → Flask API (puerto 8080) → PostgreSQL
                                      ↓
                                   Redis ← Celery Worker
```

### Estructura del Proyecto

```
Backend_Biblioteca_Soa/
├── app/
│   ├── auth/          # Autenticación
│   ├── users/         # Gestión de usuarios
│   ├── catalog/       # Catálogo de libros
│   ├── inventory/     # Control de stock
│   ├── loans/         # Préstamos
│   ├── waitlist/      # Lista de espera
│   ├── notification/  # Notificaciones
│   ├── reports/       # Reportes y dashboard
│   └── common/        # Código compartido
├── infrastructure/
│   ├── celery_app.py  # Configuración Celery
│   ├── events.py      # Sistema de eventos
│   └── dlq.py         # Dead Letter Queue
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Modelos Principales

- **Credential**: Autenticación (email, password)
- **UserProfile**: Datos de usuario (DNI, teléfono, universidad)
- **Book**: Información de libros (título, autor, ISBN)
- **Inventory**: Control de stock (copias disponibles)
- **Loan**: Préstamos (fechas, estado)
- **Waitlist**: Lista de espera (estado: PENDING, HELD, CONFIRMED)
- **Notification**: Notificaciones del sistema

### Tareas Asíncronas (Celery)

- ✅ Verificación de préstamos vencidos (cada hora)
- ✅ Recordatorios de fechas de vencimiento
- ✅ Procesamiento de lista de espera
- ✅ Limpieza de reservas expiradas
- ✅ Sistema de eventos pub/sub

---

## 🎯 Características Recientes (v2.0.0)

### 📸 Imagen de Perfil
- Sube imagen de perfil (PNG, JPG, JPEG, GIF, WEBP)
- Tamaño máximo: 5MB
- Nombres únicos con UUID
- Eliminación automática de imagen anterior

### 🔄 Cache Inteligente
- Dashboard con cache de 5 minutos
- Invalidación automática después de:
  - Crear/devolver/renovar préstamo
  - Agregar/cancelar/confirmar reserva
- Garantiza datos en tiempo real

---

## 🔒 Seguridad

- ✅ Contraseñas hasheadas (Werkzeug)
- ✅ JWT con access y refresh tokens
- ✅ Blacklist de tokens en logout
- ✅ Validación de datos (Pydantic)
- ✅ CORS configurado en gateway
- ✅ Variables de entorno para secretos

---

## 📖 Documentación Adicional

- **TRAEFIK_SETUP.md**: Configuración detallada del API Gateway
- **insomnia_collection.json**: Colección de pruebas de API
- **.env.example**: Template de variables de entorno

---

## 📞 Contacto y Soporte

Para preguntas o problemas:
1. Revisa logs: `docker-compose logs -f api`
2. Verifica servicios: `docker-compose ps`
3. Health check: `http://localhost/health`

---

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles

---

**Versión:** 2.0.0  
**Última Actualización:** Diciembre 2025  
**Estado:** ✅ Producción
