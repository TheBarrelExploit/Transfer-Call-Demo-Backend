from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import get_settings
#from auth.interfaces.web.v1.routers import auth_router_v1

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