# Basecamp Integration Setup Guide

## Prerequisites

- MongoDB running locally or via Atlas
- Python 3.9+ with backend dependencies installed
- Valid Basecamp API credentials

---

## Step 1: Get Basecamp API Token

1. Go to [Basecamp Integrations](https://launchpad.37signals.com/integrations)
2. Create a new integration or use an existing one
3. Copy the **Access Token**
4. Note your **Account ID** (visible in Basecamp URL: `https://3.basecamp.com/ACCOUNT_ID/...`)
5. Note your **Project IDs** (visible in project URLs)

---

## Step 2: Configure Environment

Add to your `.env` file:

```env
# --- Basecamp API ---
BASECAMP_ACCESS_TOKEN="your_access_token_here"
BASECAMP_ACCOUNT_ID="3222742"
BASECAMP_PROJECT_IDS="41106708,37845892,37425961"
BASECAMP_USER_AGENT="Basecamp Export (your_email@example.com)"
BASECAMP_SYNC_INTERVAL=86400
```

---

## Step 3: Initial Full Import

Run this **ONCE** to fetch all historical data:

```bash
cd backend
python scripts/basecamp_initial_import.py
```

This will:
- ✅ Fetch ALL data from configured Basecamp projects
- ✅ Queue documents for RAG embedding pipeline (ChromaDB)
- ✅ Set sync state in MongoDB (for incremental syncs)

---

## Step 4: Verify Setup

Start the backend and check status:

```bash
# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check Basecamp status (requires auth token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/v1/automation/basecamp/status
```

---

## Daily Automatic Sync

The scheduler automatically syncs Basecamp every **24 hours**, fetching only **new data** since last sync.

### Manual Sync Commands

```bash
# Incremental sync (only new data)
curl -X POST -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/automation/basecamp/sync

# Full sync (reset and fetch all)
curl -X POST -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/automation/basecamp/sync?full_sync=true"

# Reset sync state (next sync will be full)
curl -X POST -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/automation/basecamp/reset
```

---

## Data Flow

```
Basecamp API → basecamp.py → Message Queue → Processor → ChromaDB
                    ↓
              MongoDB (sync state only)
```

| Storage | What's Stored |
|---------|---------------|
| MongoDB | Sync timestamps (`basecamp_sync_state` collection) |
| ChromaDB | Embedded document vectors for RAG |

---

## Troubleshooting

### "Basecamp not configured"
Check that `.env` has all required variables and restart server.

### Rate Limited (429)
The service automatically handles rate limits with retry logic.

### Token Expired
Basecamp tokens expire. Generate a new one from Launchpad.
