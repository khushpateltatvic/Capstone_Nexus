import sys
import os
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

try:
    print("Verifying imports...")
    from app.main import app
    from app.core.config import settings
    from app.services.ingestion.watchdog import watchdog
    from app.services.intelligence.agents.router import RouterAgent
    print("✅ Core imports successful.")
    
    print("Verifying directory structure...")
    expected_dirs = [
        "backend/app/core",
        "backend/app/api/v1/endpoints",
        "backend/app/services/ingestion/parsers",
        "backend/app/services/intelligence/agents",
        "backend/app/models/domain"
    ]
    root = Path(__file__).parent.parent
    for d in expected_dirs:
        if (root / d).exists():
            print(f"✅ {d} exists.")
        else:
            print(f"❌ {d} MISSING!")

    print("\nProject Nexus Structure Verification Complete.")

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Verification Error: {e}")
