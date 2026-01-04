from app.model.base_model import Base
from app.core.database import engine
from app.model.user import User
from app.model.documents import Document
from app.model.chunks import Chunk


def create_tables():
    Base.metadata.create_all(bind = engine)