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
# _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# def get_chroma():
#     """
#     Returns a LangChain Chroma vectorstore connected to the Chroma server.
#     """
#     client = chromadb.HttpClient(
#         host=os.getenv("CHROMA_SERVER_HOST", "rag_chroma"),
#         port=int(os.getenv("CHROMA_SERVER_PORT", 8000)),
#     )

#     return Chroma(
#         client=client,
#         embedding_function=_embeddings,
#         # Collection name can be whatever you want — one per app is fine
#         collection_name="rag_collection",
#     )

# app/vector_store/chroma_client.py

import os
import time
import chromadb
from chromadb.utils import embedding_functions
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def get_chroma():
    """
    Connects to the Chroma server with retry logic and proper timeout.
    """
    chroma_url = os.getenv("CHROMA_SERVER_URL", "http://rag_chroma:8000")

    # Create the HTTP client with increased timeout and no auth assumptions
    client_settings = chromadb.config.Settings(
        chroma_server_host=os.getenv("CHROMA_SERVER_HOST", "rag_chroma"),
        chroma_server_http_port=int(os.getenv("CHROMA_SERVER_PORT", "8000")),
        anonymized_telemetry=True,
        allow_reset=False,
        # Important: disable auth checks that cause early failure
        chroma_client_auth_provider=None,
        chroma_client_auth_credentials=None,
    )

    client = chromadb.HttpClient(settings=client_settings)

    # Simple heartbeat to wait until server is ready (optional but robust)
    max_retries = 10
    for i in range(max_retries):
        try:
            client.heartbeat()  # This is a lightweight health check
            break
        except Exception as e:
            if i == max_retries - 1:
                raise ValueError(f"Could not connect to Chroma server at {chroma_url} after {max_retries} attempts. Is it running?") from e
            time.sleep(2 ** i)  # Exponential backoff: 1s, 2s, 4s...

    return Chroma(
        client=client,
        embedding_function=_embeddings,
        collection_name="rag_collection",  # Change if you use a different one
    )