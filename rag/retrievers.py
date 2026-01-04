import os
from elasticsearch import Elasticsearch

from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import ElasticSearchBM25Retriever
from langchain_classic.retrievers import ContextualCompressionRetriever

from rag.reranker import modal_reranker


def build_retriever(document_ids: list[str] | None):
    if not document_ids:
        raise ValueError("No document_ids provided for retrieval")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    # -------------------------
    # Dense Retriever (Chroma)
    # -------------------------
    dense = Chroma(
        persist_directory="db/chroma_files",
        embedding_function=embeddings,
    ).as_retriever(
        search_kwargs={
            "k": 10,
            "filter": {
                "document_id": {"$in": document_ids}
            },
        }
    )

    # -------------------------
    # Sparse Retriever (Elasticsearch BM25)
    # -------------------------
    es = Elasticsearch(
        hosts=os.getenv("ELASTIC_URL", "http://localhost:9200")
    )

    sparse = ElasticSearchBM25Retriever(
        client=es,
        index_name="research-papers",
        search_kwargs={
            "filter": {
                "terms": {
                    "document_id": document_ids
                }
            }
        },
    )

    # -------------------------
    # Hybrid Ensemble
    # -------------------------
    ensemble = EnsembleRetriever(
        retrievers=[dense, sparse],
        weights=[0.6, 0.4],
    )

    # -------------------------
    # Reranking
    # -------------------------
    return ContextualCompressionRetriever(
        base_retriever=ensemble,
        base_compressor=modal_reranker,
    )
