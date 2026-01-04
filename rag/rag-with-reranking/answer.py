import os
from dotenv import load_dotenv
import requests
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.documents import Document
from elasticsearch import Elasticsearch

from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import ElasticSearchBM25Retriever

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    convert_to_messages,
)
from langchain_core.prompts import ChatPromptTemplate

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv(override=True)

current_dir = os.path.dirname(os.path.abspath(__file__))

PERSISTANT_DIR = os.path.join(current_dir, "db", "chroma_files")
ELASTIC_URL = os.getenv("ELASTIC_URL", "http://143.198.106.253:9200")
INDEX_NAME = "research-papers"

RETRIEVAL_K = 10

# -------------------------------------------------
# EMBEDDINGS
# -------------------------------------------------
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# -------------------------------------------------
# DENSE RETRIEVER (CHROMA)
# -------------------------------------------------
dense_retriever = Chroma(
    persist_directory=PERSISTANT_DIR,
    embedding_function=embeddings,
).as_retriever(
    search_kwargs={"k": RETRIEVAL_K}
)

# -------------------------------------------------
# SPARSE RETRIEVER (ELASTICSEARCH BM25) - EXISTING INDEX
# -------------------------------------------------
es_client = Elasticsearch(ELASTIC_URL)

bm25_retriever = ElasticSearchBM25Retriever(
    client=es_client,
    index_name=INDEX_NAME,
)

# -------------------------------------------------
# HYBRID ENSEMBLE RETRIEVER
# -------------------------------------------------
ensemble_retriever = EnsembleRetriever(
    retrievers=[dense_retriever, bm25_retriever],
    weights=[0.6, 0.4],
)

# -------------------------------------------------
# OUR OWN DEPLOYED RERANKER USING CROSS-ENCODER BAAI/bge-reranker-large deployed on MODAL
# -------------------------------------------------

class ModalCrossEncoder(BaseDocumentCompressor):
    endpoint_url: str

    def compress_documents(self, documents: list[Document], query: str, callbacks=None) -> list[Document]:
        doc_texts = [doc.page_content for doc in documents]

        response = requests.post(
            self.endpoint_url,
            json={"query": query, "documents": doc_texts}
        )
        response.raise_for_status()
        result = response.json()

        ranked_texts = result["ranked_docs"]

        text_to_doc = {doc.page_content: doc for doc in documents}
        reranked_docs = [
            text_to_doc[text] for text in ranked_texts if text in text_to_doc
        ]

        return reranked_docs[:10]

modal_reranker = ModalCrossEncoder(endpoint_url=os.getenv("MODAL_RERANKER_URL"))

reranking_retriever = ContextualCompressionRetriever(
    base_compressor=modal_reranker,
    base_retriever=ensemble_retriever,
)

# -------------------------------------------------
# LLM + PROMPT
# -------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini")

SYSTEM_PROMPT = """
You are a knowledgeable and helpful assistant.
You are answering questions about research papers.

Use the provided context if relevant.
If the answer cannot be found in the context, say you do not know.

Context:
{context}
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("user", "{question}"),
    ]
)

# -------------------------------------------------
# RAG FUNCTIONS
# -------------------------------------------------
def combined_question(question: str, history: list[dict] = []) -> str:
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question if prior else question


def fetch_context(question: str) -> list:
    return reranking_retriever.invoke(question)


def answer_question(
    question: str,
    history: list[dict] = [],
) -> tuple[str, list]:
    combined = combined_question(question, history)

    docs = fetch_context(combined)
    context = "\n\n".join(doc.page_content for doc in docs)

    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return response.content, docs


# -------------------------------------------------
# LOCAL TEST
# -------------------------------------------------
if __name__ == "__main__":
    question = "What is YOLO-World and how does it work?"

    answer, docs = answer_question(question)

    print("\n=== ANSWER ===\n")
    print(answer)

    print("\n=== CONTEXT SOURCES ===\n")
    for i, d in enumerate(docs[:5]):
        print(f"[{i}] {d.metadata}")