import os
from dotenv import load_dotenv

from elasticsearch import Elasticsearch

from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
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

RETRIEVAL_K = 10  # Both retrievers will return up to 10 docs

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

# Note: This retriever returns top 10 results by default (hard-coded "size": 10)
# No need to set .k — it doesn't exist and isn't needed here.

# -------------------------------------------------
# HYBRID ENSEMBLE RETRIEVER
# -------------------------------------------------
ensemble_retriever = EnsembleRetriever(
    retrievers=[dense_retriever, bm25_retriever],
    weights=[0.6, 0.4],  # favor dense; adjust as needed
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
    return ensemble_retriever.invoke(question)


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