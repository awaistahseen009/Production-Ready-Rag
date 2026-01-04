import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv(override=True)

ELASTIC_URL = os.getenv("ELASTIC_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ELASTIC_INDEX", "research-papers")

es = Elasticsearch(
    ELASTIC_URL,
    request_timeout=120,
    max_retries=3,
    retry_on_timeout=True,
)

def get_es():
    return es

def get_index_name():
    return INDEX_NAME
