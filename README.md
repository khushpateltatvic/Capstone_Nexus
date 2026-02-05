# 📊 Project Nexus: AI-Powered Account Intelligence Platform

> **One Source of Truth for Every Account** - A comprehensive intelligence platform that consolidates unstructured data from multiple sources into actionable insights using AI and RAG.

## 🎯 Project Overview

**Project Nexus** is an enterprise-grade intelligence platform designed to consolidate and intelligently manage unstructured account data (emails, documents, notes, messages) into a singular, evolving "One Source of Truth" architecture. It leverages advanced AI, real-time ingestion, vector search, and role-based access control to deliver granular account intelligence at scale.

### Core Philosophy
- **Strict Data Scoping**: Every account maintains exactly **7 Living Documents** (Universal, Operations, Technical, Commercial, Strategy, Marketing, Miscellaneous)
- **Consolidated State Management**: Multiple unstructured sources are merged using LLM state-managers into evolving, indexed records
- **Granular RBAC**: Access controlled via Global Role Matrix with Project-specific assignment overrides
- **Real-time Intelligence**: Continuous ingestion, processing, and retrieval of account intelligence

---

## 🏗️ Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Sources                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Basecamp    │  │   Gmail      │  │ Google Drive │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         Backend Services (FastAPI + Python 3.12)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Ingestion Engine (Watchdog + Processor)                 │  │
│  │  - Real-time file watching                              │  │
│  │  - Document processing pipeline                         │  │
│  │  - Async queue management                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AI Intelligence Layer                                   │  │
│  │  - LangChain + LangGraph for orchestration              │  │
│  │  - Groq LLM (Llama 3 70B) for reasoning                 │  │
│  │  - Google Gemini for embeddings                         │  │
│  │  - RAG for context retrieval                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Layer                                              │  │
│  │  - MongoDB (Beanie ODM) - Document Store               │  │
│  │  - ChromaDB / Pinecone - Vector Store                  │  │
│  │  - In-memory caching (APScheduler + Nest Asyncio)      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Security & Access Control                               │  │
│  │  - JWT Authentication (HS256)                           │  │
│  │  - Granular RBAC system                                 │  │
│  │  - Bcrypt password hashing                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Automation & Scheduling                                 │  │
│  │  - APScheduler for job scheduling                       │  │
│  │  - Startup automation checks                            │  │
│  │  - Basecamp sync automation (24h intervals)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Frontend (React + TypeScript + Vite)               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  UI Components (Radix UI + TailwindCSS)                 │  │
│  │  - Dashboard with charts (Recharts)                     │  │
│  │  - Project & account views                              │  │
│  │  - Chat interface                                        │  │
│  │  - Real-time notifications (Sonner)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  State Management (Zustand)                              │  │
│  │  - Global authentication state                          │  │
│  │  - User preferences                                      │  │
│  │  - Real-time updates                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Backend Stack
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI 0.110.0+ | High-performance async API |
| **Server** | Uvicorn 0.27.0+ | ASGI application server |
| **Language** | Python 3.12+ | Core backend language |
| **Database** | MongoDB | Document store with Beanie ODM |
| **Vector Store** | ChromaDB / Pinecone | Semantic search & RAG |
| **LLM Framework** | LangChain + LangGraph | AI orchestration & workflows |
| **Primary LLM** | Groq (Llama 3.3 70B) | Core reasoning model |
| **Fallback LLMs** | Llama 3.1, Mixtral 8x7B | Model redundancy |
| **Embeddings** | Google Gemini / HuggingFace | Text vectorization |
| **Authentication** | JWT + Bcrypt | Secure auth & passwords |
| **Task Scheduling** | APScheduler | Cron-like automation |
| **Data Processing** | BeautifulSoup4, PyPDF | Document parsing |
| **File Formats** | python-docx, pypdf | Office document handling |

### Frontend Stack
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | React 19.2.0 | UI library |
| **Language** | TypeScript | Type-safe frontend |
| **Build Tool** | Vite | Fast build & dev server |
| **UI Components** | Radix UI | Accessible component library |
| **Styling** | TailwindCSS | Utility-first CSS |
| **Form Handling** | React Hook Form + Zod | Type-safe forms |
| **State Management** | Zustand | Lightweight global state |
| **Charts** | Recharts | Data visualization |
| **HTTP Client** | Axios | API communication |
| **Notifications** | Sonner | Toast notifications |
| **Markdown** | React Markdown | Rich text rendering |
| **Theme** | next-themes | Light/dark mode |

### DevOps & Deployment
| Component | Technology |
|-----------|-----------|
| **Containerization** | Docker (Multi-stage builds) |
| **Orchestration** | Docker Compose (dev & prod) |
| **Process Management** | APScheduler |
| **CORS** | FastAPI CORSMiddleware |

---

## 📋 Key Features

### 1. **Intelligent Data Ingestion**
- Real-time watchdog service for file monitoring
- Async document processing pipeline
- Multi-source integration:
  - Basecamp projects and messages
  - Gmail inbox scanning
  - Google Drive file monitoring
  - Local file uploads
- Automatic document classification and extraction

### 2. **AI-Powered Intelligence**
- **LLM-based State Management**: Consolidates disparate data into unified account views
- **Retrieval-Augmented Generation (RAG)**: Semantic search across all ingested data
- **Multi-model Support**: Groq with fallback options for resilience
- **Real-time Chat Interface**: Query accounts with context-aware responses
- **Marketing Extraction**: Automated extraction of commercial & marketing insights

### 3. **Vector Search & Retrieval**
- Dual vector store support (ChromaDB for dev, Pinecone for production)
- Semantic similarity search across documents
- Chunked processing for optimal retrieval
- Embedding caching for performance

### 4. **Role-Based Access Control (RBAC)**
- Global role matrix (Admin, Manager, Analyst, Viewer)
- Project-level role overrides
- Granular permission checks on all endpoints
- Audit logging for compliance

### 5. **Living Document Architecture**
Each account maintains 7 dynamic documents:
- **Universal**: Account overview & key stakeholders
- **Operations**: Day-to-day operational details
- **Technical**: Technical architecture & systems
- **Commercial**: Deal terms, pricing, contracts
- **Strategy**: Strategic initiatives & roadmap
- **Marketing**: Market positioning & messaging
- **Miscellaneous**: Other relevant information

### 6. **Automation & Scheduling**
- Startup automation checks
- Basecamp sync automation (24-hour intervals)
- Email polling and processing
- Scheduled report generation
- Custom automation workflows

### 7. **Security & Authentication**
- JWT-based authentication (24-hour tokens)
- Bcrypt password hashing
- CORS configuration
- Environment-based secrets management
- Granular endpoint authorization

---

## 📂 Project Structure

### Backend Directory Structure
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/           # 25+ CRUD & discovery endpoints
│   │       │   ├── auth.py          # Authentication endpoints
│   │       │   ├── projects.py      # Project management
│   │       │   ├── chat.py          # Chat interface
│   │       │   ├── ingestion.py     # Data ingestion
│   │       │   ├── knowledge.py     # Knowledge base
│   │       │   ├── universal_context.py
│   │       │   ├── operations.py
│   │       │   ├── technical.py
│   │       │   ├── commercial.py
│   │       │   ├── strategy.py
│   │       │   ├── marketing.py
│   │       │   ├── dashboard.py
│   │       │   ├── reports.py
│   │       │   ├── access_control.py
│   │       │   └── ... (15+ more)
│   │       ├── api.py               # Router aggregator
│   │       └── __init__.py
│   │
│   ├── agents/                      # AI Agents
│   │   ├── extractors.py           # Data extraction agents
│   │   ├── classifiers.py          # Classification agents
│   │   └── ...
│   │
│   ├── models/
│   │   ├── domain/                 # Data models for 7 documents
│   │   │   ├── project.py
│   │   │   ├── universal_context.py
│   │   │   ├── operations.py
│   │   │   ├── technical.py
│   │   │   ├── commercial.py
│   │   │   ├── strategy.py
│   │   │   ├── marketing.py
│   │   │   └── stakeholder.py
│   │   ├── persistence/            # Database models
│   │   └── schemas/                # Pydantic validation schemas
│   │
│   ├── services/
│   │   ├── ingestion/
│   │   │   ├── watchdog.py        # File monitoring service
│   │   │   ├── processor.py       # Document processing
│   │   │   └── ingestion_service.py
│   │   │
│   │   ├── intelligence/
│   │   │   ├── rag/               # RAG pipeline
│   │   │   ├── extractors.py      # Extraction logic
│   │   │   └── ...
│   │   │
│   │   ├── automation/            # Automation workflows
│   │   │   ├── startup_automation.py
│   │   │   └── basecamp_automation.py
│   │   │
│   │   ├── access_control.py      # RBAC implementation
│   │   ├── chat_service.py        # Chat logic
│   │   ├── vector_store.py        # Vector DB abstraction
│   │   ├── context_manager.py     # Context management
│   │   └── ...
│   │
│   ├── core/
│   │   ├── config.py              # Configuration settings
│   │   ├── database.py            # Database connection
│   │   ├── logging_config.py      # Logging setup
│   │   ├── security.py            # Security utilities
│   │   └── scheduler.py           # Job scheduling
│   │
│   └── __init__.py
│
├── scripts/                        # Development & utility scripts
│   ├── seed_and_populate.py       # Data seeding
│   ├── test_*.py                  # Various test scripts
│   ├── verify_*.py                # Verification scripts
│   ├── comprehensive_seed_and_trigger.py
│   └── ... (25+ utility scripts)
│
├── main.py                         # Entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image
├── docker-compose.yml              # Production compose
├── docker-compose.dev.yml          # Dev compose
├── deploy.sh                       # Deployment script
└── README.md                       # Backend docs
```

### Frontend Directory Structure
```
frontend-2/
├── src/
│   ├── components/
│   │   ├── Login.tsx              # Authentication UI
│   │   ├── Sidebar.tsx            # Navigation
│   │   ├── Dashboard.tsx          # Main dashboard
│   │   ├── ui/                    # Radix UI components
│   │   └── ... (project-specific components)
│   │
│   ├── api/                       # API client services
│   │   └── axiosInstance.ts       # Axios configuration
│   │
│   ├── store/
│   │   └── useStore.ts            # Zustand state store
│   │
│   ├── hooks/                     # React custom hooks
│   ├── utils/                     # Utility functions
│   ├── assets/                    # Images, fonts, etc.
│   │
│   ├── App.tsx                    # Root component
│   └── main.tsx                   # Entry point
│
├── public/                        # Static assets
├── package.json                   # Dependencies
├── vite.config.ts                 # Vite configuration
├── tailwind.config.js             # TailwindCSS config
├── tsconfig.json                  # TypeScript config
└── README.md                      # Frontend docs
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.12+** (backend)
- **Node.js 18+** (frontend)
- **MongoDB 5.0+** (local or Atlas)
- **Docker & Docker Compose** (optional, for containerized deployment)
- API Keys:
  - Groq API key
  - Google API key (for Gemini & Gmail)
  - Pinecone API key (optional, if using Pinecone)
  - Basecamp API token (optional)

### Backend Setup

#### 1. Clone & Navigate
```bash
cd Project_Nexus/backend
```

#### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
# Database
MONGO_CONNECTION_STRING=mongodb://localhost:27017
DATABASE_NAME=project_nexus

# API
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI & LLM
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
LLM_MODEL=gemini-1.5-flash

# Optional: Basecamp Integration
BASECAMP_ACCESS_TOKEN=your_token
BASECAMP_ACCOUNT_ID=your_account_id
BASECAMP_PROJECT_IDS=project1,project2

# Optional: Pinecone Vector Store
VECTOR_STORE_PROVIDER=chroma  # or pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=project-nexus

# Feature Flags
ENABLE_BASECAMP=true
ENABLE_GMAIL=true
ENABLE_DRIVE=true
ENABLE_LOCAL_FILES=true
ENABLE_STARTUP_AUTOMATION=true
```

#### 5. Run Backend
```bash
# Development with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`
- Docs: `http://localhost:8000/docs` (Swagger UI)
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

### Frontend Setup

#### 1. Navigate to Frontend Directory
```bash
cd Project_Nexus/frontend-2
```

#### 2. Install Dependencies
```bash
npm install
```

#### 3. Development Environment
Create or update `.env.local` if needed for API endpoints.

#### 4. Run Frontend
```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint check
npm run lint
```

The frontend will be available at `http://localhost:5173` (Vite default)

### Docker Setup (Recommended for Production)

#### Using Docker Compose
```bash
cd Project_Nexus/backend

# Development environment
docker-compose -f docker-compose.dev.yml up

# Production environment
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Using Makefile
```bash
# Quick development start
make quick-start

# Development with background
make dev-bg

# Production deployment
./deploy.sh prod

# Monitoring
make monitor
```

---

## 📡 API Overview

### Core Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - Logout

#### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{project_id}` - Get project details
- `PUT /api/v1/projects/{project_id}` - Update project
- `DELETE /api/v1/projects/{project_id}` - Delete project

#### Living Documents (7 sections)
- `GET /api/v1/projects/{project_id}/universal` - Universal context
- `GET /api/v1/projects/{project_id}/operations` - Operations
- `GET /api/v1/projects/{project_id}/technical` - Technical info
- `GET /api/v1/projects/{project_id}/commercial` - Commercial details
- `GET /api/v1/projects/{project_id}/strategy` - Strategy
- `GET /api/v1/projects/{project_id}/marketing` - Marketing
- `GET /api/v1/projects/{project_id}/misc` - Miscellaneous

#### Chat & Intelligence
- `POST /api/v1/chat` - Send message (RAG-powered)
- `GET /api/v1/chat/{project_id}` - Get chat history
- `POST /api/v1/search` - Semantic search

#### Data Ingestion
- `POST /api/v1/ingest` - Ingest new document
- `GET /api/v1/ingestion/status` - Ingestion status
- `POST /api/v1/ingestion/sync-basecamp` - Manual Basecamp sync

#### Access Control
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/roles` - List roles
- `PUT /api/v1/projects/{project_id}/assign-role` - Assign role

#### Reports & Analytics
- `GET /api/v1/reports` - Generate reports
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/dashboard/insights` - Account insights

---

## 🔄 Core Workflows

### 1. Document Ingestion Pipeline
```
Source Data (Email, File, etc.)
    ↓
[Watchdog Service] - Monitors for new files
    ↓
[Document Parser] - Extracts text, metadata
    ↓
[Text Splitter] - Chunks document (LangChain)
    ↓
[Embedder] - Creates vectors (Gemini/HF)
    ↓
[Vector Store] - Stores in ChromaDB/Pinecone
    ↓
[Context Manager] - Updates project documents
    ↓
[Document Complete] ✓
```

### 2. Chat & RAG Query Pipeline
```
User Message
    ↓
[Vector Search] - Find relevant documents
    ↓
[Context Assembly] - Build context window
    ↓
[Prompt Construction] - Format with instructions
    ↓
[LLM Call] - Groq (with fallback models)
    ↓
[Response Generation] - Stream to frontend
    ↓
[Chat Saved] - Store in conversation history
```

### 3. State Consolidation Workflow
```
Multiple Source Documents
    ↓
[Extraction Agent] - Identify key information
    ↓
[Classification Agent] - Categorize by section
    ↓
[Merge Agent] - Combine and deduplicate
    ↓
[Update Document] - Store consolidated state
    ↓
[Index for Search] - Vector embed updated document
```

---

## 🔐 Security Architecture

### Authentication Flow
1. User submits credentials (email + password)
2. Password verified against bcrypt hash
3. JWT token generated with HS256 algorithm
4. Token includes user ID, role, project assignments
5. Token expires after 24 hours
6. Client stores token in localStorage
7. Token sent in `Authorization: Bearer <token>` header

### Authorization (RBAC)
```
User Request
    ↓
[Verify JWT] - Check token validity
    ↓
[Extract Role] - Get user's global role
    ↓
[Check Permissions] - Verify against role matrix
    ↓
[Project Override] - Check project-specific role
    ↓
[Resource Access] - Grant/deny access
    ↓
[Audit Log] - Record access attempt
```

### Global Role Matrix
| Role | Permissions |
|------|------------|
| **Admin** | Full access to all features, user management |
| **Manager** | Create/edit projects, assign roles, view all data |
| **Analyst** | View/edit assigned projects, limited user access |
| **Viewer** | Read-only access to assigned projects |

---

## 🤖 AI & Intelligence Components

### LLM Integration
- **Primary Model**: Groq Llama 3.3 70B (fast, reasoning)
- **Fallback Models**: Llama 3.1 70B, Mixtral 8x7B (for resilience)
- **Embedding Model**: Google Gemini or HuggingFace (sentence-transformers)
- **Framework**: LangChain + LangGraph for orchestration

### Prompt Engineering
- **System Prompts**: Role-specific instructions for agents
- **Context Windows**: Optimal chunk sizes for retrieval
- **Few-Shot Examples**: Enhanced reasoning patterns
- **Chain-of-Thought**: Structured reasoning for complex queries

### RAG (Retrieval-Augmented Generation)
- Hybrid retrieval (semantic + keyword)
- Vector similarity search
- Reranking for relevance
- Context assembly with metadata
- Query expansion and clarification

---

## 📊 Monitoring & Logging

### Logging Setup
- Structured logging with timestamps
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log files in `logs/` directory
- Real-time console output in development

### Health Checks
- `GET /health` - Service health status
- Database connection tests
- Vector store connectivity
- External API availability

### Metrics
- Request/response times
- Ingestion queue size
- Vector search latency
- Token usage tracking

---

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Specific test file
pytest tests/test_auth.py

# With coverage
pytest --cov=app tests/

# Verbose output
pytest -v
```

### Frontend Tests
```bash
# Unit tests (if configured)
npm test

# Type checking
npm run lint
```

### Integration Tests
```bash
# Comprehensive end-to-end test
python scripts/test_e2e.py

# Basecamp integration test
python scripts/test_basecamp_sync.py

# Chat API test
python scripts/verify_chat_api.py
```

---

## 🚨 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check MongoDB connection
python scripts/check_mongo.py

# Verify environment variables
printenv | grep -E "GROQ|GOOGLE|MONGO"

# Check port availability
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

#### Vector Store Issues
```bash
# Check ChromaDB size
python scripts/check_chroma_size.py

# Debug RAG extraction
python scripts/debug_rag_extraction.py

# Verify embeddings
python scripts/test_embedding_pipeline.py
```

#### API Connection Issues
```bash
# Test all endpoints
python scripts/test_all_endpoints.py

# Verify JWT tokens
python scripts/verify_debug.py

# Check Basecamp connectivity
python scripts/simple_basecamp_test.py
```

#### Database Issues
```bash
# Diagnose database
python scripts/diagnose_db.py

# Check project data
python scripts/check_project_data.py

# Debug MongoDB
python scripts/debug_mongo.py
```

---

## 📚 Additional Resources

### Documentation
- [Backend README](backend/README.md) - Backend-specific documentation
- [Frontend README](frontend-2/README.md) - Frontend-specific documentation
- [Containerization Guide](backend/CONTAINERIZATION.md) - Docker setup
- [Basecamp Setup](backend/docs/BASECAMP_SETUP.md) - Basecamp integration
- [Postman Collection](backend/Project_Nexus_Consolidated.postman_collection.json) - API testing

### Utility Scripts
- `seed_and_populate.py` - Populate test data
- `comprehensive_seed_and_trigger.py` - Full automation test
- `list_models.py` - Available LLM models
- `test_chroma.py` - Vector store testing
- `verify_rbac.py` - RBAC verification

---

## 🔄 Development Workflow

### Making Changes
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes in backend/frontend
3. Test thoroughly
4. Commit with clear messages
5. Push and create pull request

### Code Standards
- **Python**: PEP 8, type hints
- **TypeScript**: ESLint, strict mode
- **Frontend**: Component-driven development
- **Backend**: Service layer architecture

---

## 📦 Deployment

### Development
```bash
make quick-start
```

### Production
```bash
./deploy.sh prod
```

### Environment-Specific Settings
- **Development**: SQLite/Local ChromaDB, debug logging
- **Production**: MongoDB/Pinecone, optimized logging

---

## 🤝 Contributing

1. Follow code standards
2. Write tests for new features
3. Update documentation
4. Test in Docker before pushing

---

## 📝 License

[Add your license information here]

---

## 📧 Support & Contact

For issues, questions, or feature requests, please contact the development team.

---

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Enhanced AI reasoning (multi-agent systems)
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Custom automation rules engine
- [ ] Third-party integrations (Slack, Teams)
- [ ] GraphQL API support
- [ ] Advanced audit logging

---

**Made with ❤️ for enterprise intelligence**
