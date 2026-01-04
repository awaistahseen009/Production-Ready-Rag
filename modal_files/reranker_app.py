import modal
from pydantic import BaseModel

image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git")
    .pip_install(
        "torch==2.3.0",
        "sentence-transformers==2.7.0",
        "pydantic",
    )
)

app = modal.App("hf-reranker-new", image=image)

class RerankRequest(BaseModel):
    query: str
    documents: list[str]

@app.cls(gpu="T4", image=image, timeout=600)
class Reranker:
    @modal.enter()
    def load_model(self):
        from sentence_transformers import CrossEncoder
        import torch
        print("Loading BAAI/bge-reranker-large on GPU...")
        self.model = CrossEncoder(
            "BAAI/bge-reranker-large",
            device="cuda" if torch.cuda.is_available() else "cpu",
            max_length=512,
        )
        print("Model loaded successfully!")

    @modal.fastapi_endpoint(method="POST")
    def rerank(self, request: RerankRequest):
        pairs = [[request.query, doc] for doc in request.documents]
        scores = self.model.predict(pairs)
        ranked = sorted(
            zip(request.documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return {
            "ranked_docs": [doc for doc, _ in ranked],
            "scores": [float(score) for _, score in ranked],
        }