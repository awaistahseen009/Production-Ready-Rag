import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from typing import List

from .base_model import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name: Mapped[str] = mapped_column(String(30))
    last_name: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(1024))

    documents: Mapped[List["Document"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
