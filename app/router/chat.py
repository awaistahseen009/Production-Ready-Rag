from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.model.chats import Chat
from app.model.messages import ChatMessage
from app.schemas.chat import ChatCreate, ChatResponse
from app.utils.protected_route import get_current_user
from rag.retrievers import build_retriever
from rag.pipeline import run_rag
from rag.title_generator import generate_chat_title

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


# =========================================================
# CREATE NEW CHAT (FIRST MESSAGE)
# POST /chat
# =========================================================
@chat_router.post("", response_model=ChatResponse)
def create_chat(
    payload: ChatCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # ---- Guard: documents required ----
    if not payload.document_ids:
        raise HTTPException(
            status_code=400,
            detail="Please select documents to chat"
        )

    # ---- Create chat ----
    title = generate_chat_title(payload.message)
    chat = Chat(title=title, user_id=user.id)
    db.add(chat)
    db.commit()
    db.refresh(chat)

    # ---- RAG ----
    retriever = build_retriever(
        document_ids=[str(d) for d in payload.document_ids]
    )

    answer, docs = run_rag(
        payload.message,
        history=[],
        retriever=retriever,
    )

    # ---- Save messages ----
    db.add_all([
        ChatMessage(chat_id=chat.id, role="user", content=payload.message),
        ChatMessage(chat_id=chat.id, role="assistant", content=answer),
    ])
    db.commit()

    return {
        "chat_id": chat.id,
        "title": chat.title,
        "answer": answer,
        "sources": docs,
    }


# =========================================================
# CONTINUE EXISTING CHAT
# POST /chat/{chat_id}
# =========================================================
@chat_router.post("/{chat_id}", response_model=ChatResponse)
def continue_chat(
    chat_id: UUID,
    payload: ChatCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    chat = (
        db.query(Chat)
        .filter(Chat.id == chat_id, Chat.user_id == user.id)
        .first()
    )

    if not chat:
        raise HTTPException(404, "Chat not found")

    # ---- History (last 20) ----
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )

    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(messages)
    ]

    # ---- RAG ----
    retriever = build_retriever(
        document_ids=[str(d) for d in payload.document_ids]
        if payload.document_ids
        else None
    )

    answer, docs = run_rag(
        payload.message,
        history=history,
        retriever=retriever,
    )

    # ---- Save messages ----
    db.add_all([
        ChatMessage(chat_id=chat.id, role="user", content=payload.message),
        ChatMessage(chat_id=chat.id, role="assistant", content=answer),
    ])
    db.commit()

    return {
        "chat_id": chat.id,
        "title": chat.title,
        "answer": answer,
        "sources": docs,
    }
