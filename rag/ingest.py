import os
import shutil
from dotenv import load_dotenv

from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader

load_dotenv(override=True)

current_dir = os.path.dirname(os.path.abspath(__file__))
PERSISTENT_DIR = os.path.join(current_dir, "db", "chroma_files")

# Load PDFs
loader = PyPDFDirectoryLoader(
    path="../data/papers",
    glob="*.pdf"
)
documents = loader.load()

# Split documents
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=300
)
docs = splitter.split_documents(documents)
print(f"We have total chunks: {len(docs)}")

# Reset DB if exists
if os.path.exists(PERSISTENT_DIR):
    shutil.rmtree(PERSISTENT_DIR)

# Create embeddings + Chroma DB
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

db = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory=PERSISTENT_DIR
)
