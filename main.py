import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.shared.config import get_settings
#from auth.interfaces.web.v1.routers import auth_router_v1
from src.auth.infrastructure.security import get_password_hash


#get settings from environment variables
settings = get_settings()

app = FastAPI(
    title= settings.APP_NAME,
    description="FastAPI Transfer Call",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
#app.include_router(auth_router_v1, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Transfer-Call-Demo API is running"}


""" 
@app.on_event("startup")
async def startup_db_client():
    # Código temporal para crear usuario de prueba
    users_collection = db["users"]
    await users_collection.insert_one({
        "username": "admin",
        "hashed_password": get_password_hash("secret"),
        "email": "admin@example.com",
        "disabled": False
    }) """
if __name__ == "__main__":
    try:
        subprocess.run(["fastapi","dev","main.py","--port", str(settings.PORT), "--reload"])
    except KeyboardInterrupt:
        print("Server stopped.")