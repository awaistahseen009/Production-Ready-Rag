import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
import chromadb
load_dotenv(override=True)

# app/vectorstore/chroma_client.py
# CURRENT_FILE = os.path.abspath(__file__)

# # project_root/
# PROJECT_ROOT = os.path.dirname(
#     os.path.dirname(
#         os.path.dirname(CURRENT_FILE)
#     )
# )

# PERSIST_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

# _embeddings = OpenAIEmbeddings(
#     model="text-embedding-3-small"
# )

# def get_chroma():
#     return Chroma(
        
#         persist_directory=PERSIST_DIR,
#         embedding_function=_embeddings,
#     )
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def get_chroma():
    """
    Returns a LangChain Chroma vectorstore connected to the Chroma server.
    """
    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_SERVER_HOST", "rag_chroma"),
        port=int(os.getenv("CHROMA_SERVER_PORT", 8000)),
    )

    return Chroma(
        client=client,
        embedding_function=_embeddings,
        # Collection name can be whatever you want — one per app is fine
        collection_name="rag_collection",
    )
