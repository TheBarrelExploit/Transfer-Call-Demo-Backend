import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.shared.config import get_settings
from src.shared.database.mongodb import MongoDB
from contextlib import asynccontextmanager
#from auth.interfaces.web.v1.routers import auth_router_v1
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