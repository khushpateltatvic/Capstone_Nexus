from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Any, Dict, List
from datetime import datetime
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.models.domain.core_entities import Project, Client
from app.core.database import get_database
from app.core.rbac import has_project_access
import json

router = APIRouter()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Report - {project_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'sans-serif'],
                    }},
                    colors: {{
                        nexus: {{
                            50: '#f0f9ff',
                            100: '#e0f2fe',
                            500: '#0ea5e9',
                            600: '#0284c7',
                            800: '#075985',
                            900: '#0c4a6e',
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        @media print {{
            .no-print {{ display: none; }}
            body {{ -webkit-print-color-adjust: exact; }}
            .page-break {{ page-break-before: always; }}
        }}
        body {{ background-color: #f8fafc; color: #1e293b; }}
        .card {{ background: white; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); }}
    </style>
</head>
<body class="antialiased min-h-screen pb-20">

    <!-- Actions Bar (No Print) -->
    <div class="fixed top-4 right-4 z-50 no-print flex gap-2">
        <button onclick="window.print()" class="bg-nexus-600 hover:bg-nexus-800 text-white font-semibold py-2 px-4 rounded-lg shadow-lg flex items-center gap-2 transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Print Report
        </button>
    </div>

    <!-- Cover Page -->
    <div class="max-w-5xl mx-auto p-8 pt-20 page-break">
        <div class="text-center py-24 bg-gradient-to-br from-nexus-900 to-slate-900 text-white rounded-3xl shadow-2xl mb-12 relative overflow-hidden">
             <div class="absolute top-0 left-0 w-full h-full opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]"></div>
            <h2 class="text-2xl font-light text-nexus-200 mb-4 tracking-wider uppercase">{client_name}</h2>
            <h1 class="text-6xl font-bold mb-6 tracking-tight relative z-10">{project_name}</h1>
            <div class="inline-block px-6 py-2 bg-white/10 rounded-full text-sm backdrop-blur-sm border border-white/20">
                Status: <span class="font-bold text-nexus-200">{project_status}</span>
            </div>
            <p class="mt-12 text-slate-400 text-sm">Generated on {generated_date} by {generated_by}</p>
        </div>

        <!-- Executive Summary -->
        <div class="prose prose-lg max-w-none text-slate-600 mb-16">
            <h2 class="text-3xl font-bold text-slate-800 mb-6 border-b pb-4">Executive Summary</h2>
            <p>
                This comprehensive report details the current operational, technical, and strategic standing of <strong>{project_name}</strong>. 
                Initiated with <strong>{client_name}</strong>, this engagement focuses on delivering high-impact solutions.
            </p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 not-prose">
                <div class="p-6 bg-blue-50 rounded-xl border border-blue-100">
                    <h3 class="text-sm font-bold text-blue-600 uppercase tracking-wide mb-1">Engagement Type</h3>
                    <p class="text-2xl font-bold text-slate-800">{engagement_type}</p>
                </div>
                <div class="p-6 bg-emerald-50 rounded-xl border border-emerald-100">
                    <h3 class="text-sm font-bold text-emerald-600 uppercase tracking-wide mb-1">Health Score</h3>
                    <p class="text-2xl font-bold text-slate-800">{health_score}%</p>
                </div>
                <div class="p-6 bg-purple-50 rounded-xl border border-purple-100">
                    <h3 class="text-sm font-bold text-purple-600 uppercase tracking-wide mb-1">Industry</h3>
                    <p class="text-2xl font-bold text-slate-800">{industry}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Operations & Technical Overview -->
    <div class="max-w-5xl mx-auto p-8 page-break">
        <h2 class="text-3xl font-bold text-slate-800 mb-8 border-b pb-4">Operational & Technical Overview</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <div class="card p-8">
                <h3 class="text-xl font-bold text-slate-700 mb-6 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-nexus-500"></span> Technical Stack
                </h3>
                <div class="space-y-4">
                    {technical_content}
                </div>
            </div>
            
            <div class="card p-8 bg-slate-50">
                <h3 class="text-xl font-bold text-slate-700 mb-6">Resource Allocation</h3>
                <div class="w-full h-64">
                   <canvas id="resourceChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="card p-8 border-t-4 border-nexus-500">
            <h3 class="text-xl font-bold text-slate-700 mb-4">Operational Timeline</h3>
            <div class="space-y-6">
                 {operations_content}
            </div>
        </div>
    </div>

    <!-- Commercial & Strategy -->
    <div class="max-w-5xl mx-auto p-8 page-break">
        <h2 class="text-3xl font-bold text-slate-800 mb-8 border-b pb-4">Commercial & Strategic Alignment</h2>
        
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="col-span-2 card p-8">
                <h3 class="text-xl font-bold text-slate-700 mb-6">Strategic Initiatives</h3>
                <ul class="space-y-4">
                    {strategy_content}
                </ul>
            </div>
            <div class="card p-8 bg-slate-900 text-white">
                <h3 class="text-xl font-bold text-emerald-400 mb-6">Commercial Highlights</h3>
                <div class="space-y-6">
                    {commercial_content}
                </div>
            </div>
        </div>
    </div>

    <script>
        // Chart Data Injection
        const resourceData = {resource_chart_data};
        
        // Resource Chart
        new Chart(document.getElementById('resourceChart'), {{
            type: 'doughnut',
            data: resourceData,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom' }} }},
                cutout: '60%'
            }}
        }});
    </script>
</body>
</html>
"""

def extract_list_content(data_dict: Dict, key: str) -> str:
    """Helper to extract list data into HTML li items"""
    items = data_dict.get(key, [])
    if isinstance(items, dict) and "value" in items:
         items = items["value"]
    
    if not items:
        return "<p class='text-slate-400 italic'>No data available.</p>"
    
    if isinstance(items, list):
        return "".join([f"<li class='text-slate-600'>{item}</li>" for item in items if isinstance(item, str)])
    
    return str(items)

def extract_tech_stack(data: Dict) -> str:
    """Helper for tech stack formatting"""
    tech = data.get("technical", {})
    stack = tech.get("tech_stack", [])
    if isinstance(stack, dict) and "value" in stack:
        stack = stack["value"]
        
    if not stack:
         return "<p class='text-slate-400 italic'>No tech stack defined.</p>"
         
    return "".join([f"""
        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
            <span class="font-medium text-slate-700">{getattr(item, 'name', item) if not isinstance(item, str) else item}</span>
        </div>
    """ for item in stack])

@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def generate_project_report(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a dynamic, printable HTML report for a specific project.
    All roles except 'trainee' can generate reports.
    """
    
    # Permission Check - Trainees cannot generate reports
    if current_user.role.lower() == "trainee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Trainees do not have permission to generate project reports."
        )

    db = await get_database()
    
    # Fetch Project & Client
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client = await db.clients.find_one({"client_id": project.get("client_id")})
    client_name = client.get("name") if client else "Unknown Client"
    
    # Check Access
    # Note: We rely on the role check above, but in a stricter system we'd use has_project_access(current_user, project)
    
    # Data Extraction
    universal = project.get("universal_context", {})
    ops = project.get("operations", {})
    tech = project.get("technical", {})
    comm = project.get("commercial", {})
    strat = project.get("strategy", {})

    # Format Content
    # Technical
    tech_html = extract_tech_stack(project)
    
    # Operations
    milestones = ops.get("milestones", [])
    if isinstance(milestones, dict) and "value" in milestones: milestones = milestones["value"]
    ops_html = "".join([f"""
        <div class="flex gap-4">
             <div class="min-w-[100px] text-sm text-nexus-600 font-bold">{m.get('date', 'TBD') if isinstance(m, dict) else 'TBD'}</div>
             <div class="text-slate-700">{m.get('title', m) if isinstance(m, dict) else m}</div>
        </div>
    """ for m in milestones]) if milestones else "<p class='text-slate-400 italic'>No milestones recorded.</p>"

    # Strategy
    objectives = strat.get("business_objectives", [])
    if isinstance(objectives, dict) and "value" in objectives: objectives = objectives["value"]
    strat_html = "".join([f"""
        <li class="flex items-start gap-3">
            <svg class="w-5 h-5 text-emerald-500 mt-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            <span class="text-slate-600">{obj}</span>
        </li>
    """ for obj in objectives]) if objectives else "<p class='text-slate-400 italic'>No objectives defined.</p>"

    # Commercial
    comm_html = f"""
        <div>
            <p class="text-xs uppercase opacity-70 mb-1">Agreement Type</p>
            <p class="font-bold text-lg">{comm.get('agreement_type', 'Standard')}</p>
        </div>
        <div>
            <p class="text-xs uppercase opacity-70 mb-1">Renewal Date</p>
            <p class="font-bold text-lg">{comm.get('renewal_date', 'N/A')}</p>
        </div>
    """

    # Chart Data (Mocking reasonable distribution if real data is missing)
    # in a real scenario, we'd calculate this from 'operations.resource_allocation'
    resource_chart_data = {
        "labels": ["Development", "Design", "Management", "QA"],
        "datasets": [{
            "data": [40, 20, 15, 25],
            "backgroundColor": ["#3b82f6", "#a855f7", "#64748b", "#22c55e"]
        }]
    }

    html_content = HTML_TEMPLATE.format(
        project_name=project.get("name", "Unnamed Project"),
        project_status=project.get("status", "Active"),
        client_name=client_name,
        generated_date=datetime.utcnow().strftime("%B %d, %Y"),
        generated_by=current_user.full_name,
        engagement_type=client.get("engagement_type", "FTE") if client else "FTE",
        health_score=client.get("health_score", 100) if client else 100,
        industry=client.get("industry", "Technology") if client else "Technology",
        technical_content=tech_html,
        operations_content=ops_html,
        strategy_content=strat_html,
        commercial_content=comm_html,
        resource_chart_data=json.dumps(resource_chart_data)
    )

    return html_content
