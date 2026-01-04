import os
import requests
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.documents import Document

class ModalCrossEncoder(BaseDocumentCompressor):
    endpoint_url: str

    def compress_documents(self, documents, query, callbacks=None):
        texts = [d.page_content for d in documents]

        r = requests.post(
            self.endpoint_url,
            json={"query": query, "documents": texts},
            timeout=60,
        )
        r.raise_for_status()

        ranked = r.json()["ranked_docs"]
        lookup = {d.page_content: d for d in documents}

        return [lookup[t] for t in ranked if t in lookup][:10]

modal_reranker = ModalCrossEncoder(
    endpoint_url=os.getenv("MODAL_RERANKER_URL")
)
