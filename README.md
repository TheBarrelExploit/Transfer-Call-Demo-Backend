# Transfer Call Demo — Backend (Demo Tarificador)

API REST construida con **FastAPI** y **MongoDB** para la tarificación de llamadas: consulta y reporte de llamadas, gestión de tarifas con cambios programados, administración de usuarios, autenticación (JWT, MFA y SSO con Microsoft) y envío de reportes por correo.

## Tabla de contenido

- [Características](#características)
- [Tecnologías](#tecnologías)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [Endpoints](#endpoints)
- [Tareas programadas](#tareas-programadas)
- [Autores y licencia](#autores-y-licencia)

## Características

- **Autenticación**: login local con JWT, autenticación multifactor (TOTP con código QR y códigos de respaldo) e inicio de sesión con Microsoft (Entra ID / MSAL).
- **Usuarios**: creación, actualización, cambio de contraseña, listado y eliminación.
- **Tarificador**: consulta de llamadas por rango de fechas, origen, destino, tipo y clase de llamada; reportes generales y por número.
- **Tarifas (prices)**: consulta de tarifas vigentes e históricas, creación y actualización con cambios programados mediante APScheduler.
- **Dashboard**: resumen de consumo por entidad.
- **Envío de correos**: envío de reportes, recuperación de contraseña y notificación de creación de usuario con plantillas HTML.

## Tecnologías

| Área | Librerías |
| --- | --- |
| Framework web | FastAPI, Starlette, Uvicorn |
| Base de datos | MongoDB (Motor asíncrono, PyMongo) |
| Configuración | pydantic-settings, python-dotenv |
| Seguridad | python-jose / PyJWT, passlib + bcrypt, pyotp, qrcode, MSAL |
| Tareas programadas | APScheduler (job store en MongoDB) |
| Datos y reportes | Polars, Pandas, fastexcel, openpyxl |
| Correo | fastapi-mail, aiosmtplib, Jinja2 |

## Arquitectura

El proyecto sigue una **arquitectura hexagonal (puertos y adaptadores)** organizada por módulos de dominio:

```
.
├── main.py                     # Punto de entrada: app FastAPI, lifespan, CORS y routers
├── requirements.txt
└── src/
    ├── auth/                   # Login, JWT, MFA y SSO Microsoft
    ├── users/                  # Gestión de usuarios
    ├── tarificador/            # Consulta y reportes de llamadas
    ├── prices/                 # Tarifas e historial de precios
    ├── dashboard/              # Resumen por entidad
    ├── datasend/               # Envío de correos y plantillas HTML
    ├── scheduled_tasks/        # Tareas auxiliares
    └── shared/                 # Configuración, MongoDB, APScheduler, excepciones y recursos
```

Cada módulo se divide en capas:

- `domain/` — entidades, modelos y puertos (interfaces).
- `application/` — servicios y casos de uso.
- `infrastructure/` — repositorios MongoDB, seguridad, integraciones externas e inyección de dependencias.
- `interfaces/web/v1/` — routers y esquemas (Pydantic) de la API.

## Requisitos

- Python 3.11 o superior
- MongoDB (local o Atlas)
- Una cuenta SMTP para el envío de correos (por defecto Gmail con contraseña de aplicación)
- Un registro de aplicación en Microsoft Entra ID para el SSO

## Instalación

```bash
git clone https://github.com/TheBarrelExploit/Transfer-Call-Demo-Backend.git
```

```bash
cd Transfer-Call-Demo-Backend
```

```bash
python -m venv .venv
```

Activa el entorno virtual (`.venv\Scripts\activate` en Windows o `source .venv/bin/activate` en Linux/macOS) e instala las dependencias:

```bash
pip install -r requirements.txt
```

> `uvloop` no es compatible con Windows; si la instalación falla, elimínalo de `requirements.txt`.

## Configuración

Crea un archivo `.env` en la raíz del proyecto (ver [src/shared/config.py](src/shared/config.py)):

```env
# General
APP_NAME="FastAPI Transfer Call"
PORT=8000
DEBUG=true
ALLOWED_HOSTS=["http://localhost:5500","http://127.0.0.1:5500"]

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=tarificador

# Microsoft SSO
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_TENANT_ID=
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/auth/microsoft/callback

# JWT
JWT_SECRET=cambia-este-valor
JWT_ALGORITHM=HS256
JWT_EXPIRATION=60

# Correo (fastapi-mail)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

Las variables `MONGO_*`, `MICROSOFT_*`, `JWT_*`, `MAIL_USERNAME`, `MAIL_PASSWORD` y `MAIL_FROM` son obligatorias; el resto tiene valores por defecto.

## Ejecución

Modo desarrollo (recarga automática):

```bash
fastapi dev main.py
```

Modo producción (usa el puerto definido en `PORT`):

```bash
python main.py
```

Al iniciar, la aplicación:

1. Se conecta a MongoDB.
2. Carga la plantilla de reportes `src/shared/reportes.xlsx`.
3. Inicia APScheduler con persistencia de trabajos en la colección `jobs`.
4. Crea un usuario de prueba `testuser` si no existe (**solo para desarrollo**; elimínalo o cambia su contraseña en otros entornos).

La API se sirve bajo el `root_path` `/api`. Documentación interactiva:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Los logs se escriben en consola y en `app.log`.

## Endpoints

Todas las rutas tienen el prefijo `/api/v1`.

| Módulo | Prefijo | Endpoints principales |
| --- | --- | --- |
| Auth | `/auth` | `POST /token`, `POST /login`, `GET /me`, `POST /logout`, `GET /login/microsoft`, `GET /microsoft/callback`, `GET /mfa/status`, `POST /mfa/setup`, `POST /mfa/enable`, `POST /mfa/verify`, `POST /mfa/toggle` |
| Usuarios | `/users` | `POST /create_user`, `PUT /change_password`, `PUT /update_user`, `GET /user_all`, `DELETE /delete_user/{user_id}` |
| Llamadas | `/calls` | `GET /call_all`, `GET /call_by_date_range`, `GET /call_by_originational`, `GET /call_by_connected`, `GET /call_by_type_of_call`, `GET /call_by_class_call`, `GET /call_by_kind_of_call`, `POST /call_by`, `GET /general_report`, `GET /general_report_all`, `POST /report_number` |
| Tarifas | `/prices` | `GET /prices_all`, `GET /prices_by`, `GET /prices_history_all`, `GET /prices_history_by`, `POST /price_create`, `PUT /price_update` |
| Dashboard | `/dashboard` | `GET /entity_sumary` |
| Correo | `/emailsend` | `POST /send-report-email`, `POST /password-recovery` |

Los endpoints protegidos requieren el encabezado `Authorization: Bearer <token>`.

## Tareas programadas

Las actualizaciones de tarifas (`PUT /prices/price_update`) se registran en la colección `prices_changes` y se programan con APScheduler. Al cumplirse la fecha, la tarea [execute_price_change](src/shared/apscheduler/tarea_precios.py) aplica los nuevos valores en la colección `price` y guarda el registro en `price history`. Los trabajos persisten en MongoDB, por lo que sobreviven a reinicios del servidor.

## Autores y licencia

- Denuar Andrés Ramos Lezama
- Paola Andrea Morales Rodríguez

© 2025. Todos los derechos reservados. Código desarrollado exclusivamente con fines de demostración; consulta [LICENSE.txt](LICENSE.txt).
