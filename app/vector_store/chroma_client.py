import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings

load_dotenv(override=True)

# app/vectorstore/chroma_client.py
CURRENT_FILE = os.path.abspath(__file__)

# project_root/
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(CURRENT_FILE)
    )
)

PERSIST_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

def get_chroma():
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=_embeddings,
    )
