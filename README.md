# Production Ready RAG

A production-grade Retrieval-Augmented Generation (RAG) system built with FastAPI, featuring advanced hybrid search with reranking, user authentication, document management, and conversational AI capabilities.

## Overview

Production Ready RAG is a complete RAG application that combines dense vector search (ChromaDB), sparse retrieval (Elasticsearch BM25), and neural reranking to deliver highly accurate document-based question answering. The system includes user authentication, asynchronous document processing, and a chat interface with conversation history.

## Key Features

- **Advanced RAG Pipeline**: Hybrid retrieval combining dense embeddings and BM25 with neural reranking
- **User Authentication**: JWT-based signup/login system with secure password hashing
- **Document Management**: Upload, process, retrieve, and delete PDF documents
- **Conversational AI**: Multi-turn chat with conversation history and automatic title generation
- **Asynchronous Processing**: Background document chunking and embedding via Celery
- **Production Infrastructure**: Docker Compose setup with Redis, Elasticsearch, and FastAPI
- **Evaluated Architecture**: Benchmarked against vanilla RAG and hybrid RAG approaches

## Architecture

### RAG Pipeline

The system implements a three-stage retrieval pipeline:

1. **Dense Retrieval (ChromaDB)**: Semantic search using OpenAI embeddings (text-embedding-3-small)
2. **Sparse Retrieval (Elasticsearch)**: Keyword-based BM25 search
3. **Hybrid Ensemble**: Combines dense (60%) and sparse (40%) retrievers
4. **Neural Reranking**: Cross-encoder reranking using BAAI/bge-reranker-large via Modal

This architecture was chosen after evaluation experiments showed it outperforms:
- Vanilla RAG (dense retrieval only)
- Hybrid RAG (without reranking)

Evaluation results are available in `rag/evaluation_results/`.

### System Components

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼───┐ ┌──▼──┐  ┌────▼────┐ ┌──▼──────┐
│ Auth  │ │ Docs│  │  Chat   │ │ Celery  │
│Router │ │Router│  │ Router  │ │ Worker  │
└───────┘ └──┬──┘  └────┬────┘ └────┬────┘
             │          │           │
        ┌────┴──────────┴───────────┴────┐
        │                                 │
   ┌────▼─────┐                    ┌─────▼─────┐
   │PostgreSQL│                    │   Redis   │
   └──────────┘                    └───────────┘
        │
   ┌────┴──────────────┬──────────────┐
   │                   │              │
┌──▼────┐        ┌─────▼──────┐  ┌───▼──────────┐
│ChromaDB│        │Elasticsearch│  │   Supabase   │
└────────┘        └────────────┘  └──────────────┘
```

### Database Schema

- **Users**: Authentication and user profiles
- **Documents**: PDF metadata and processing status
- **Chunks**: Document chunks stored in PostgreSQL (content in vector stores)
- **Chats**: Conversation sessions with auto-generated titles
- **ChatMessages**: Individual messages in conversations

## Technology Stack

### Backend
- **FastAPI**: Modern async web framework
- **SQLAlchemy**: ORM for PostgreSQL
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker and result backend
- **Alembic**: Database migrations

### RAG & AI
- **LangChain**: RAG orchestration framework
- **OpenAI**: GPT-4o-mini for chat, text-embedding-3-small for embeddings
- **ChromaDB**: Vector database for dense retrieval
- **Elasticsearch**: Full-text search with BM25
- **Modal**: Serverless GPU deployment for reranker
- **Sentence Transformers**: Cross-encoder reranking model

### Storage
- **PostgreSQL (Neon)**: Primary database
- **Supabase Storage**: PDF file storage
- **ChromaDB**: Local vector store persistence

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Uvicorn**: ASGI server

## Installation

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL database (or use provided Neon connection)
- OpenAI API key
- Cohere API key (optional, for alternative embeddings)
- Modal account (for reranker deployment)

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd production-ready-rag
```

2. Create a `.env` file in the root directory:
```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Elasticsearch
ELASTIC_URL=http://localhost:9200

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256

# Supabase Storage
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
SUPABASE_BUCKET=your_bucket_name

# Modal Reranker
MODAL_RERANKER_URL=your_modal_endpoint_url

# Optional
COHERE_API_KEY=your_cohere_api_key
```

3. **Load environment variables (Optional):**

   If you want to load all `.env` variables into your system environment:

   **Linux/Mac:**
   ```bash
   set -o allexport; source .env; set +o allexport
   ```

   **Windows (PowerShell):**
   ```powershell
   Get-Content .env | ForEach-Object {
       if ($_ -match '^([^=]+)=(.*)$') {
           [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
       }
   }
   ```

   **Windows (CMD):**
   ```cmd
   for /f "tokens=*" %i in (.env) do set %i
   ```

   Note: The application automatically loads `.env` using `python-dotenv`, so this step is only needed if you want the variables available system-wide.

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. **Start Redis and Elasticsearch:**

   **Option A: Using Docker (Recommended for local development)**
   ```bash
   docker-compose up redis elasticsearch
   ```

   **Option B: Use cloud services**
   - Update `REDIS_URL` in `.env` with your Redis cloud URL
   - Update `ELASTIC_URL` in `.env` with your Elasticsearch cloud URL

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the FastAPI server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. Start Celery worker (in a separate terminal):
```bash
celery -A app.core.celery.celery_app worker --loglevel=info
```

**Note:** If running Redis and Elasticsearch via Docker Compose, they will be available at:
- Redis: `redis://localhost:6379/0`
- Elasticsearch: `http://localhost:9200`

### Docker Deployment

1. Build and start all services:
```bash
docker-compose up --build
```

This will start:
- FastAPI application (port 8000)
- Redis (internal)
- Elasticsearch (port 9200)

2. The API will be available at `http://localhost:8000`

3. API documentation: `http://localhost:8000/docs`

### Deploy Reranker to Modal

1. Install Modal CLI:
```bash
pip install modal
```

2. Authenticate:
```bash
modal token new
```

3. Deploy the reranker:
```bash
modal deploy modal_files/reranker_app.py
```

4. Copy the endpoint URL to your `.env` file as `MODAL_RERANKER_URL`

## API Endpoints

### Authentication

#### POST `/auth/signup`
Register a new user.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "username": "johndoe",
  "password": "securepassword123",
  "confirm_password": "securepassword123"
}
```

**Response:**
```json
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com"
}
```

#### POST `/auth/login`
Authenticate and receive JWT token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Documents

All document endpoints require authentication via Bearer token.

#### POST `/documents/upload`
Upload one or more PDF documents.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:** Multipart form data with PDF files

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "document.pdf",
    "url": "https://storage.url/document.pdf",
    "processed_status": "pending"
  }
]
```

#### GET `/documents/`
Get all documents for the authenticated user.

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "document.pdf",
    "url": "https://storage.url/document.pdf",
    "processed_status": "completed"
  }
]
```

#### GET `/documents/{document_id}`
Get a specific document by ID.

#### DELETE `/documents/{document_id}`
Delete a document and all associated chunks from vector stores.

### Chat

#### POST `/chat`
Start a new chat conversation.

**Request Body:**
```json
{
  "message": "What is the main topic of the paper?",
  "document_ids": ["uuid1", "uuid2"]
}
```

**Response:**
```json
{
  "chat_id": "uuid",
  "title": "Main Topic Discussion",
  "answer": "The paper discusses...",
  "sources": ["chunk1 content", "chunk2 content"]
}
```

#### POST `/chat/{chat_id}`
Continue an existing conversation.

**Request Body:**
```json
{
  "message": "Can you elaborate on that?",
  "document_ids": ["uuid1", "uuid2"]
}
```

### Health Check

#### GET `/health`
Check API health status.

**Response:**
```json
{
  "status": "Healthy"
}
```

## How It Works

### Document Upload Flow

1. User uploads PDF via `/documents/upload`
2. File is stored in Supabase Storage
3. Document record created in PostgreSQL with `pending` status
4. Celery task `preprocess_document` is triggered asynchronously
5. Task downloads PDF, splits into chunks (1000 chars, 300 overlap)
6. Chunks are embedded and stored in:
   - ChromaDB (with OpenAI embeddings)
   - Elasticsearch (for BM25 indexing)
7. Chunk metadata saved to PostgreSQL
8. Document status updated to `completed`

### Chat Flow

1. User sends message with document IDs
2. System builds hybrid retriever filtered by document IDs
3. Dense retriever fetches top-10 semantically similar chunks
4. Sparse retriever fetches top-10 BM25-ranked chunks
5. Ensemble combines results (60% dense, 40% sparse)
6. Modal reranker re-scores and returns top-10 most relevant chunks
7. Context is formatted and sent to GPT-4o-mini with conversation history
8. Response is generated and saved to database
9. Chat title is auto-generated on first message

### Retrieval Pipeline Details

**Dense Retrieval (ChromaDB)**
- Embedding model: `text-embedding-3-small`
- Retrieves top-10 chunks by cosine similarity
- Filtered by document IDs

**Sparse Retrieval (Elasticsearch)**
- BM25 algorithm for keyword matching
- Retrieves top-10 chunks
- Filtered by document IDs

**Ensemble**
- Combines results with 60/40 weighting
- Handles duplicate chunks

**Reranking**
- Model: `BAAI/bge-reranker-large`
- Deployed on Modal with T4 GPU
- Cross-encoder scores query-document pairs
- Returns top-10 reranked results

## Evaluation Results

The system was rigorously evaluated across 323 test cases comparing three RAG approaches.

### Test Categories

The evaluation dataset includes 6 question categories designed to test different RAG capabilities:

1. **Direct Fact**: Straightforward factual questions with clear answers found in a single location
   - Example: "What is the capital of France?"
   - Tests basic retrieval and factual accuracy

2. **Temporal**: Questions involving time, dates, chronological order, or temporal relationships
   - Example: "When was the paper published?" or "What happened after the experiment?"
   - Tests temporal reasoning and date extraction

3. **Numerical**: Questions requiring numerical data, statistics, or quantitative information
   - Example: "What was the accuracy score?" or "How many participants were in the study?"
   - Tests numerical extraction and calculation

4. **Spanning**: Questions whose answers require information from multiple documents or sections
   - Example: "Compare the methodologies used in papers X and Y"
   - Tests multi-document retrieval and synthesis

5. **Holistic**: Questions requiring understanding of overall themes, conclusions, or big-picture concepts
   - Example: "What is the main contribution of this research?"
   - Tests comprehension and summarization abilities

6. **Relationship**: Questions about connections, dependencies, or relationships between entities or concepts
   - Example: "How does concept A relate to concept B?" or "What is the relationship between X and Y?"
   - Tests relational reasoning across chunks

These categories ensure comprehensive evaluation of the RAG system's ability to handle diverse query types.

### Retrieval Performance Comparison

| Metric | Vanilla RAG | Hybrid RAG | RAG with Reranking |
|--------|-------------|------------|-------------------|
| **MRR** (Mean Reciprocal Rank) | 0.566 | 0.593 | **0.628** ✓ |
| **nDCG** (Normalized DCG) | 0.586 | 0.609 | **0.641** ✓ |
| **Keyword Coverage** | 73.6% | **77.6%** ✓ | 76.2% |

**Key Findings:**
- RAG with Reranking achieves the highest MRR (+11% vs vanilla, +6% vs hybrid)
- Best nDCG score, indicating superior ranking quality
- Hybrid RAG shows slight edge in keyword coverage due to BM25

![MRR by Category](rag/evaluation_results/rag-with-reranking-eval_20260102_102105/retrieval/mrr_by_category_matplotlib.png)

### Answer Quality Comparison

| Metric | Vanilla RAG | Hybrid RAG | RAG with Reranking |
|--------|-------------|------------|-------------------|
| **Accuracy** | **4.44/5** ✓ | 4.43/5 | 4.41/5 |
| **Completeness** | **4.07/5** ✓ | 3.98/5 | 3.93/5 |
| **Relevance** | 4.61/5 | **4.62/5** ✓ | 4.60/5 |
| **Faithfulness** | 4.41/5 | **4.48/5** ✓ | 4.42/5 |
| **Context Relevance** | 4.60/5 | 4.64/5 | **4.65/5** ✓ |
| **Context Utilization** | 4.18/5 | **4.21/5** ✓ | 4.14/5 |
| **Unsupported Claims** | 0.59 | **0.50** ✓ | 0.54 |

**Key Findings:**
- All three approaches achieve high answer quality (>4.4/5 accuracy)
- Hybrid RAG shows best faithfulness with fewest unsupported claims
- RAG with Reranking provides best context relevance
- Differences are marginal in answer quality, but significant in retrieval

### Answer Quality Metrics by Category

<details>
<summary>Click to view detailed metric breakdowns</summary>

#### Accuracy by Category
![Accuracy by Category](rag/evaluation_results/rag-with-reranking-eval_20260102_102105/answers/avg_accuracy_by_category_matplotlib.png)

#### Completeness by Category
![Completeness by Category](rag/evaluation_results/rag-with-reranking-eval_20260102_102105/answers/avg_completeness_by_category_matplotlib.png)

#### Faithfulness by Category
![Faithfulness by Category](rag/evaluation_results/rag-with-reranking-eval_20260102_102105/answers/avg_faithfulness_by_category_matplotlib.png)

#### Context Relevance by Category
![Context Relevance by Category](rag/evaluation_results/rag-with-reranking-eval_20260102_102105/answers/avg_context_relevance_by_category_matplotlib.png)

</details>

### Why RAG with Reranking?

Despite similar answer quality scores, **RAG with Reranking** was chosen for production because:

1. **Superior Retrieval Quality**: 6-11% improvement in MRR/nDCG means better context is retrieved
2. **Better Ranking**: Cross-encoder reranking provides more accurate relevance scoring than vector similarity alone
3. **Scalability**: Better retrieval reduces hallucination risk as document corpus grows
4. **Future-Proof**: High-quality context retrieval is foundational for advanced RAG techniques

The marginal differences in answer quality are due to GPT-4o-mini's strong reasoning capabilities compensating for weaker retrieval in vanilla/hybrid approaches. However, better retrieval provides a more robust foundation for production use.

### Interactive Visualizations

For interactive plots, open the HTML files in your browser:
- Retrieval metrics: `rag/evaluation_results/rag-with-reranking-eval_20260102_102105/retrieval/mrr_by_category_plotly.html`
- Answer metrics: `rag/evaluation_results/rag-with-reranking-eval_20260102_102105/answers/avg_*_plotly.html`

## Project Structure

```
production-ready-rag/
├── app/
│   ├── core/
│   │   ├── celery/          # Celery configuration
│   │   ├── security/        # Auth & password hashing
│   │   └── database.py      # SQLAlchemy setup
│   ├── model/               # SQLAlchemy models
│   ├── repository/          # Database access layer
│   ├── router/              # API endpoints
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── document.py
│   ├── schemas/             # Pydantic models
│   ├── service/             # Business logic
│   ├── supabase_client/     # Supabase storage client
│   ├── tasks/               # Celery tasks
│   │   └── document_processing_task.py
│   ├── utils/               # Utilities
│   └── vector_store/        # Vector DB clients & ingestion
├── rag/
│   ├── evaluation_results/  # Benchmark results
│   │   ├── vanilla-rag/
│   │   ├── hybrid-rag/
│   │   └── rag-with-reranking/
│   ├── answer.py            # RAG answer generation
│   ├── evaluate.py          # Evaluation framework
│   ├── ingest.py            # Document ingestion
│   ├── pipeline.py          # RAG orchestration
│   ├── reranker.py          # Modal reranker client
│   ├── retrievers.py        # Hybrid retriever setup
│   └── title_generator.py  # Chat title generation
├── modal_files/
│   └── reranker_app.py      # Modal deployment for reranker
├── alembic/                 # Database migrations
├── docker-compose.yaml      # Multi-container setup
├── Dockerfile               # FastAPI container
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

## Development

### Running Evaluations

```bash
# Run evaluation on a specific test case
python rag/evaluate.py <test_number>

# Example: evaluate test case 5
python rag/evaluate.py 5
```

The evaluation framework measures:
- **Retrieval metrics**: MRR, nDCG, keyword coverage
- **Answer quality**: Accuracy, completeness, relevance, faithfulness
- **Context quality**: Context relevance and utilization

Results are saved to `rag/evaluation_results/` with CSV summaries and visualizations.

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Celery Worker

```bash
# Start worker
celery -A app.core.celery.celery_app worker --loglevel=info

# Monitor tasks
celery -A app.core.celery.celery_app flower
```

## Troubleshooting

### Elasticsearch Connection Issues
Ensure Elasticsearch is running and accessible:
```bash
curl http://localhost:9200
```

### ChromaDB Persistence
The `chroma_db` directory must be writable. In Docker, it's mounted as a volume.

### Celery Tasks Not Processing
1. Check Redis connection
2. Verify Celery worker is running
3. Check logs for errors

### Document Processing Fails
1. Verify Supabase credentials
2. Check PDF is valid and accessible
3. Review Celery worker logs

## Performance Considerations

- **Chunk Size**: 1000 characters with 300 overlap balances context and precision
- **Retrieval Count**: Top-10 from each retriever before reranking
- **Reranking**: GPU-accelerated on Modal for low latency
- **Async Processing**: Celery prevents blocking on large document uploads
- **Connection Pooling**: SQLAlchemy pool for database efficiency

## Security

- Passwords hashed with bcrypt
- JWT tokens for stateless authentication
- Environment variables for sensitive data
- SQL injection protection via SQLAlchemy ORM
- File type validation on uploads
- User-scoped document access

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, LangChain, and modern RAG techniques by Awais Tahseen.
