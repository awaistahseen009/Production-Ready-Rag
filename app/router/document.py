from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
from uuid import uuid4
from dotenv import load_dotenv
from app.vector_store.chroma_client import get_chroma
from app.vector_store.elasticsearch_client import get_es, get_index_name
from elasticsearch import helpers
from app.core.database import get_db
from app.model.documents import Document
from app.model.enums import DocumentStatus
from app.schemas.document import DocumentOut, DocumentCreate
from app.schemas.user import UserOutput
from app.utils.protected_route import get_current_user
from app.supabase_client.supabase_client import supabase
from app.tasks.document_processing_task import preprocess_document
from app.model.chunks import Chunk
load_dotenv(override=True)

document_router = APIRouter()

BUCKET_NAME = os.getenv("SUPABASE_BUCKET")
ALLOWED_FILETYPES = {"application/pdf"}

@document_router.post("/upload", response_model=List[DocumentOut])
def upload_document(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: UserOutput = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    documents: List[Document] = []

    for file in files:
        if file.content_type not in ALLOWED_FILETYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}"
            )

        file_bytes = file.file.read()
        file_ext = os.path.splitext(file.filename)[1]
        file_id = uuid4()

        storage_path = f"{user.id}/{file_id}{file_ext}"

        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": file.content_type},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)

        # -------------------------
        # Save document in DB
        # -------------------------
        document = Document(
            title=file.filename,
            url=public_url,
            user_id=user.id,
            processed_status=DocumentStatus.PENDING,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # -------------------------
        # Trigger Celery (ASYNC)
        # -------------------------
        preprocess_document.delay(str(document.id))

        documents.append(document)

    return documents

@document_router.get("/", response_model=List[DocumentOut])
def get_all_documents(
    db: Session = Depends(get_db),
    user: UserOutput = Depends(get_current_user),
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return documents

# @document_router.delete("/{document_id}", status_code=200)
# def delete_document(
#     document_id: str,
#     db: Session = Depends(get_db),
#     user: UserOutput = Depends(get_current_user),
# ):
#     document = (
#         db.query(Document)
#         .filter(
#             Document.id == document_id,
#             Document.user_id == user.id,
#         )
#         .first()
#     )

#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")

#     # -------------------------
#     # Fetch chunk IDs
#     # -------------------------
#     chunks = (
#         db.query(Chunk.id)
#         .filter(Chunk.document_id == document.id)
#         .all()
#     )

#     chunk_ids = [str(c[0]) for c in chunks]

#     # -------------------------
#     # Delete from Chroma
#     # -------------------------
#     if chunk_ids:
#         chroma_ids = [f"{document_id}_{cid}" for cid in chunk_ids]
#         vectorstore = get_chroma()
#         vectorstore.delete(ids=chroma_ids)

#     # -------------------------
#     # Delete from Elasticsearch
#     # -------------------------
#     if chunk_ids:
#         es = get_es()
#         index_name = get_index_name()

#         actions = [
#             {
#                 "_op_type": "delete",
#                 "_index": index_name,
#                 "_id": cid,
#             }
#             for cid in chunk_ids
#         ]

#         helpers.bulk(
#             es,
#             actions,
#             ignore_status=[404],  # ignore missing docs
#         )

#     # -------------------------
#     # Delete from DB
#     # -------------------------
#     db.query(Chunk).filter(Chunk.document_id == document.id).delete()
#     db.delete(document)
#     db.commit()

#     return {
#         "success": True,
#         "message": "Document and related chunks deleted successfully",
#         "document_id": document_id,
#     }
@document_router.delete("/{document_id}", status_code=200)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: UserOutput = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # -------------------------
    # Fetch chunk IDs
    # -------------------------
    chunk_ids = [
        str(c[0])
        for c in db.query(Chunk.id)
        .filter(Chunk.document_id == document.id)
        .all()
    ]

    # -------------------------
    # Delete from Chroma (CORRECT)
    # -------------------------
    get_chroma().delete(
        where={"document_id": str(document.id)}
    )

    # -------------------------
    # Delete from Elasticsearch
    # -------------------------
    if chunk_ids:
        helpers.bulk(
            get_es(),
            [
                {
                    "_op_type": "delete",
                    "_index": get_index_name(),
                    "_id": cid,
                }
                for cid in chunk_ids
            ],
            raise_on_error=False,
            ignore_status=[404],
        )

    # -------------------------
    # Delete from DB
    # -------------------------
    db.query(Chunk)\
      .filter(Chunk.document_id == document.id)\
      .delete(synchronize_session=False)

    db.delete(document)
    db.commit()

    return {
        "success": True,
        "document_id": document_id,
    }

@document_router.get("/{document_id}", response_model=DocumentOut)
def get_document_by_id(
    document_id: str,
    db: Session = Depends(get_db),
    user: UserOutput = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document
