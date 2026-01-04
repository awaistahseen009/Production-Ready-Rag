from app.core.celery.celery_app import celery_app
from sqlalchemy.orm import Session
from app.model.documents import Document
from app.model.chunks import Chunk
from app.model.enums import DocumentStatus
from app.core.database import get_db, SessionLocal
from app.vector_store.ingest import ingest_document_from_url
import app.model

@celery_app.task(bind=True)
def preprocess_document(self, document_id: str):
    db = SessionLocal()
    document = None  

    try:
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()

        if not document:
            return

        chunk_data = ingest_document_from_url(
            document_id=document.id,
            pdf_url=document.url,
        )

        for chunk in chunk_data:
            db.add(
                Chunk(
                    id=chunk["chunk_id"],
                    document_id=document.id,
                )
            )

        document.processed_status = DocumentStatus.COMPLETED
        db.commit()

    except Exception:
        db.rollback()

        if document is not None:
            document.processed_status = DocumentStatus.FAILED
            db.commit()

        raise

    finally:
        db.close()
