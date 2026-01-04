import uuid
import tempfile
import requests
from uuid import UUID
from typing import List, Dict

from elasticsearch import helpers
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.vector_store.chroma_client import get_chroma
from app.vector_store.elasticsearch_client import get_es, get_index_name


def ingest_document_from_url(
    document_id: UUID,
    pdf_url: str,
) -> List[Dict]:
    """
    Downloads a PDF, splits into chunks, ingests into:
    - Chroma (dense embeddings)
    - Elasticsearch (BM25)
    Returns chunk metadata for database persistence.
    """

    # -------------------------
    # Download PDF
    # -------------------------
    response = requests.get(pdf_url, timeout=60)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(response.content)
        pdf_path = tmp.name

    # -------------------------
    # Load PDF
    # -------------------------
    pages = PyPDFLoader(pdf_path).load()

    # -------------------------
    # Split into chunks
    # -------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=300,
    )
    chunks = splitter.split_documents(pages)

    chroma = get_chroma()
    es = get_es()
    index_name = get_index_name()

    chunk_records: List[Dict] = []
    es_actions = []

    # -------------------------
    # Prepare chunks
    # -------------------------
    for chunk in chunks:
        chunk_id = uuid.uuid4()
        chroma_id = f"{document_id}_{chunk_id}"

        metadata = {
            "document_id": str(document_id),
            "chunk_id": str(chunk_id),
            "source": chunk.metadata.get("source", ""),
            "page": chunk.metadata.get("page", -1),
        }

        chunk_records.append({
            "chunk_id": chunk_id,
            "document_id": document_id,
            "content": chunk.page_content,
            "chroma_id": chroma_id,
            "metadata": metadata,
        })

        es_actions.append({
            "_index": index_name,
            "_id": str(chunk_id),
            "_source": {
                "content": chunk.page_content,
                "document_id": str(document_id),
                "chunk_id": str(chunk_id),
                "source": metadata["source"],
                "page": metadata["page"],
            },
        })

    # -------------------------
    # Ingest into Chroma
    # -------------------------
    chroma.add_documents(
        documents=[
            Document(
                page_content=c["content"],
                metadata=c["metadata"],
            )
            for c in chunk_records
        ],
        ids=[c["chroma_id"] for c in chunk_records],
    )

    # -------------------------
    # Ingest into Elasticsearch
    # -------------------------
    if es_actions:
        helpers.bulk(
            es,
            es_actions,
            chunk_size=500,
            request_timeout=120,
        )

    return chunk_records
