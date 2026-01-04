from uuid import UUID
from pydantic import BaseModel

class MessageOut(BaseModel):
    role: str
    content: str
