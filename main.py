from fastapi import FastAPI , UploadFile,HTTPException , File ,  Path  , Query, Depends
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.utils.init_db import create_tables
from app.utils.protected_route import get_current_user
from app.router.auth import auth_router
from app.router.chat import chat_router
from app.router.document import document_router
from app.router.chat import chat_router
from app.schemas.user import UserOutput

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router=auth_router, tags=["auth"], prefix="/auth")
app.include_router(router =chat_router, tags=["chat"])
app.include_router(router = document_router, tags = ['document'], prefix="/documents")
app.include_router(router = chat_router, tags = ["chat"], prefix = "/chat")
@app.get("/health")
def health():
    return {"status": "Healthy"}
