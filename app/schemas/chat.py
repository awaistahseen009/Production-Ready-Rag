from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

class ChatCreate(BaseModel):
    message: str
    document_ids: Optional[List[UUID]] = None

class ChatResponse(BaseModel):
    chat_id: UUID
    title: str
    answer: str
    sources: list
