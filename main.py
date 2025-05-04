import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.shared.config import get_settings
from src.shared.database.mongodb import MongoDB
from contextlib import asynccontextmanager
from src.auth.interfaces.web.v1.routers import router as auth_router_v1
from src.auth.infrastructure.security import get_password_hash

#get settings from environment variables
settings = get_settings()

@asynccontextmanager
async def lifespan(app:FastAPI):
    """
        Lifespan event for the FastAPI application.
        Connect to MongoDB and close the connection when the app stops.
    """
    # Connect to MongoDB
    mongo = MongoDB()
    await mongo.connect(settings.MONGO_URI, settings.MONGO_DB)
    
    # Crear usuario de prueba si no existe
    users_col = mongo.get_collection("users")
    if await users_col.count_documents({"username": "testuser"}) == 0:
        from src.auth.domain.entities import User
        test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),  # Esto generará un nuevo hash válido
        disabled=False,
        full_name="Usuario de Prueba"
    )
        await users_col.insert_one(test_user.dict())

    yield
    
    # Close MongoDB connection
    await mongo.close()

app = FastAPI(
    title= settings.APP_NAME,
    description="FastAPI Transfer Call",
    version="0.1.0",
    lifespan=lifespan,
)


# CORS middleware
# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",  # El origen de frontend
        "http://localhost:5500",   # Alternativa común
        "http://127.0.0.1:8001",   # Para Swagger UI
        "http://localhost:8001"     # Para Swagger UI alternativo
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
# Incluir routers
app.include_router(auth_router_v1, prefix="/api")


@app.get("/")
async def read_root():
    mongo = MongoDB()
    collection = mongo.get_collection("llamadas")
    result = await collection.find_one({})
    print(result)
    return {"message": "Transfer-Call-Demo API is running"}


if __name__ == "__main__":
    try:
        subprocess.run(["fastapi","dev","main.py","--port", str(settings.PORT), "--reload"])
    except KeyboardInterrupt:
        print("Server stopped.")