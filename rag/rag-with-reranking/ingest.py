import os
import shutil
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader

# ---------------------------
# ENV + PATHS
# ---------------------------
load_dotenv(override=True)

current_dir = os.path.dirname(os.path.abspath(__file__))

PERSISTENT_DIR = os.path.join(current_dir, "db", "chroma_files")
PDF_DIR = "../../data/papers"

INDEX_NAME = "research-papers"
ELASTIC_URL = os.getenv("ELASTIC_URL", "http://localhost:9200")

# ---------------------------
# LOAD PDF DOCUMENTS
# ---------------------------
loader = PyPDFDirectoryLoader(
    path=PDF_DIR,
    glob="*.pdf"
)

documents = loader.load()
print(f"Loaded {len(documents)} PDF pages")

# ---------------------------
# SPLIT DOCUMENTS
# ---------------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=300
)

docs = splitter.split_documents(documents)
print(f"Total chunks created: {len(docs)}")

# ---------------------------
# RESET CHROMA (OPTIONAL)
# ---------------------------
if os.path.exists(PERSISTENT_DIR):
    shutil.rmtree(PERSISTENT_DIR)

# ---------------------------
# CREATE CHROMA VECTOR STORE
# ---------------------------
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

chroma_db = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory=PERSISTENT_DIR
)

print("Chroma DB persisted successfully")

# ---------------------------
# ELASTICSEARCH SETUP (BM25)
# ---------------------------
es = Elasticsearch(
    ELASTIC_URL,
    request_timeout=120,
    max_retries=3,
    retry_on_timeout=True
)

# Create index if not exists
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(
        index=INDEX_NAME,
        settings={
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "-1"   # IMPORTANT: disable refresh during ingest
            }
        },
        mappings={
            "properties": {
                "content": {"type": "text"},
                "source": {"type": "keyword"},
                "page": {"type": "integer"}
            }
        }
    )
    print(f"Created Elasticsearch index: {INDEX_NAME}")
else:
    print(f"Elasticsearch index already exists: {INDEX_NAME}")

# ---------------------------
# BULK INGEST INTO ELASTICSEARCH
# ---------------------------
actions = []

for i, doc in enumerate(docs):
    actions.append({
        "_index": INDEX_NAME,
        "_id": i,
        "_source": {
            "content": doc.page_content,
            "source": doc.metadata.get("source", ""),
            "page": doc.metadata.get("page", -1)
        }
    })

helpers.bulk(
    es,
    actions,
    chunk_size=500,
    request_timeout=120
)

# Re-enable refresh after ingest
es.indices.put_settings(
    index=INDEX_NAME,
    body={"index": {"refresh_interval": "1s"}}
)

print("Elasticsearch BM25 ingest completed successfully")
