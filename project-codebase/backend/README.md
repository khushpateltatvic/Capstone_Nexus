# Project Nexus: Account Intelligence Platform

Project Nexus is a high-fidelity intelligence platform designed to consolidate unstructured account data (emails, notes, documents) into a singular, evolving "One Source of Truth" architecture.

## 🚀 Core Philosophy
- **Strict Project Scoping**: Every project maintains exactly **7 Living Documents** (Universal, Operations, Technical, Commercial, Strategy, Marketing, Misc).
- **Consolidated State**: Multiple unstructured sources are merged using LLM state-managers into a single evolving record per project section.
- **Granular RBAC**: Access is controlled via a Global Role Matrix combined with Project-specific assignment overrides.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python 3.12)
- **Database**: MongoDB (Beanie ODM)
- **Intelligence**: LangChain, Groq (Llama 3 70B), LangGraph
- **Vector Search**: ChromaDB
- **Task Management**: Celery & Redis

## 📂 Project Structure
```bash
backend/
├── app/
│   ├── api/v1/         # CRUD & Discovery Endpoints
│   ├── models/domain/  # Consolidated Project Sections & Stakeholder Models
│   ├── services/       # Ingestion, Access Control, Context Management
│   ├── agents/         # LLM Classifiers & Extractors
│   └── core/           # Config, DB, Security logic
├── requirements.txt    # System dependencies
└── README.md           # Master Documentation
```

## ⚙️ Setup & Execution

### 1. Environment Configuration
Ensure you have a `.env` file in the `backend/` directory with:
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=project_nexus
GROQ_API_KEY=your_key
SECRET_KEY=your_secret
```

### 2. Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Commands
- **Start Server**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Background Worker**: `celery -A app.worker worker --loglevel=info`

## 🔄 Core Workflows

### 🟡 Ingestion Workflow
The system processes unstructured text (emails/notes) through a multi-stage pipeline:
1. **Classification**: Identifies which of the 7 sections the data belongs to.
2. **Context Retrieval**: Fetches the current state of that section for the specific project.
3. **LLM Extraction**: Merges new data with existing state, normalizing names and entities.
4. **Provenance**: Appends the contribution to a `sources` audit trail.
5. **Stakeholder Sync**: Automatically provisions/updates the `ExternalStakeholder` collection based on extracted POC/Stakeholder details.

### 🔵 Access Control Workflow
1. **Global Check**: Validates the user's role/department against the `RolePermission` matrix.
2. **Local Override**: Checks `ProjectAssignment` for custom `view_access` or `edit_access` flags.
3. **Discovery**: `GET /access/clients` and `/access/projects` return only authorized resources.

### 🟢 Stakeholder Management
- External stakeholders (POCs, Influencers) are stored project-wise in a dedicated schema.
- **List**: `GET /api/v1/stakeholders/{project_id}`
- **Manual Edit**: `PATCH /api/v1/stakeholders/{stakeholder_id}`

## 📖 API Documentation
A comprehensive Postman collection is available at `Project_Nexus_Consolidated.postman_collection.json`.
- **Total Endpoints**: 38
- **Core Sections**: Auth, Discovery, Ingestion, Project Sections (CRUD), Stakeholders, Admin.

