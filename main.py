import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.shared.config import get_settings
from src.shared.database.mongodb import MongoDB
from src.shared.apscheduler.apscheduler_config import SchedulerConfig
from contextlib import asynccontextmanager
from src.users.interfaces.web.v1.routers import router as users_router_v1
from src.auth.interfaces.web.v1.routers import router as auth_router_v1
from src.tarificador.interfaces.web.v1.routers import router as call_router_v1
from src.prices.interface.web.v1.routers import router as price_router_v1
from src.auth.infrastructure.security import get_password_hash
from pymongo import MongoClient
from dataclasses import asdict
from src.users.domain.models import UserBase, MFAConfig
from datetime import datetime, timezone
# get settings from environment variables

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event for the FastAPI application.
    Connect to MongoDB and close the connection when the app stops.
    """
    # Connect to MongoDB
    sync_mongo_client = MongoClient(settings.MONGO_URI, maxPoolSize=10)
    mongo = MongoDB()
    await mongo.connect(settings.MONGO_URI, settings.MONGO_DB)

    apscheduler = SchedulerConfig(
        mongo_client=sync_mongo_client, mongo_database_name=settings.MONGO_DB
    )
    apscheduler.start()

    app.state.mongo = mongo
    app.state.scheduler = apscheduler

    # Crear usuario de prueba si no existe
    users_col = mongo.get_collection("users")
    if await users_col.count_documents({"username": "testuser"}) == 0:
        from src.users.domain.models import UserBase, AuthProvider

        test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": get_password_hash("testpassword"),
            "entity": "test",
            "auth_provider": "local",
            "complete_profile": True,
            "roles": ["user"],
            "mfa": {
                "secret": None,
                "enabled": False,
                "backup_codes": [],
                "last_used_at": None,
            },
        }
        if await users_col.count_documents({"username": "testuser"}) == 0:
            await users_col.insert_one(test_user)
            logger.info("Usuario de prueba creado exitosamente")

    yield

    # Close MongoDB connection
    await mongo.close()
    apscheduler.shutdowm()
    sync_mongo_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI Transfer Call",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": "your-client-id",
    },
)

app.swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
}

app.openapi_components = {
    "securitySchemes": {
        "Bearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
}

# Aplica el esquema de seguridad globalmente
app.openapi_security = [{"Bearer": []}]

print(settings.ALLOWED_HOSTS)
print(settings.MICROSOFT_REDIRECT_URI)

# CORS middleware
# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_origin_regex=r"http://(127\.0\.0\.1|localhost)(:\d+)?",  # Regex para localhost con cualquier puerto
)
# Incluir routers
app.include_router(auth_router_v1, prefix="/api")
app.include_router(users_router_v1, prefix="/api")
app.include_router(call_router_v1, prefix="/api")
app.include_router(price_router_v1, prefix="/api")


@app.get("/")
async def read_root():
    mongo = MongoDB()
    collection = mongo.get_collection("llamadas")
    result = await collection.find_one({})
    print(result)
    return {"message": "Transfer-Call-Demo API is running"}


from fastapi import Request
import logging

logger = logging.getLogger(__name__)


@app.middleware("http")
async def debug_cors_middleware(request: Request, call_next):
    # Loggear información de la solicitud entrante
    logger.info(
        f"\n{'=' * 50}\nCORS DEBUG - Request Incoming\n"
        f"Origin: {request.headers.get('origin')}\n"
        f"Method: {request.method}\n"
        f"Path: {request.url.path}\n"
        f"Headers: {request.headers}\n"
        f"{'=' * 50}"
    )

    response = await call_next(request)

    # Añadir headers CORS manualmente si es necesario
    origin = request.headers.get("origin")
    if origin in [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    # Loggear información de la respuesta
    logger.info(
        f"\n{'=' * 50}\nCORS DEBUG - Response Outgoing\n"
        f"Status: {response.status_code}\n"
        f"Headers: {response.headers}\n"
        f"{'=' * 50}"
    )

    return response


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)

if __name__ == "__main__":
    try:
        subprocess.run(
            ["fastapi", "dev", "main.py", "--port", str(settings.PORT), "--reload"]
        )
    except KeyboardInterrupt:
        print("Server stopped.")
