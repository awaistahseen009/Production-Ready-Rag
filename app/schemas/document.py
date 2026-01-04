from pydantic import BaseModel, HttpUrl
from typing import List
from uuid import UUID
from app.model.enums import DocumentStatus


class DocumentCreate(BaseModel):
    user_id:UUID
    orirginal_name: str
    storage_path:str
    public_url: HttpUrl


    
class DocumentOut(BaseModel):
    id: UUID
    title: str
    url: str
    processed_status: DocumentStatus

    class Config:
        from_attributes = True

