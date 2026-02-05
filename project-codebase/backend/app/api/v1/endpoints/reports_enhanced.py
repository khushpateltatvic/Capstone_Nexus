from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Any, Dict, List
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.models.domain.core_entities import Project, Client
from app.models.domain.sections import (
    UniversalContext, Operations, TechnicalIntelligence, Commercial, 
    Strategy, Marketing, Other, Task, Blocker, TechStackItem, 
    SOW, Invoice, Stakeholder, POC
)
from app.core.database import get_database
from app.core.rbac import has_project_access
from datetime import datetime, date
import json
import math

router = APIRouter()

def extract_datapoint_value(datapoint):
    """Extract value from datapoint structure"""
    if not datapoint:
        return None
    if isinstance(datapoint, dict):
        return datapoint.get("value")
    return datapoint

def extract_nested_value(data, key_path):
    """Extract nested value from data using dot notation"""
    keys = key_path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

def calculate_completion_rate(tasks):
    """Calculate task completion rate"""
    if not tasks:
        return 0
    completed = sum(1 for task in tasks if isinstance(task, dict) and 
                   task.get("status", "").lower() in ["completed", "done", "closed"])
    return round((completed / len(tasks)) * 100, 1)

def get_status_color(status):
    """Get color based on status"""
    status_colors = {
        "active": "bg-green-500",
        "completed": "bg-blue-500", 
        "pending": "bg-yellow-500",
        "on-hold": "bg-orange-500",
        "cancelled": "bg-red-500",
        "at_risk": "bg-red-500"
    }
    return status_colors.get(status.lower().replace(" ", "_"), "bg-gray-500")

def get_traffic_light_color(light):
    """Get traffic light colors"""
    colors = {
        "green": "bg-green-500",
        "yellow": "bg-yellow-500",
        "orange": "bg-orange-500",
        "red": "bg-red-500"
    }
    return colors.get(light.lower(), "bg-gray-500")

def format_task_html(task, index):
    """Format task as HTML"""
    if not isinstance(task, dict):
        return ""
    
    status_colors = {
        "completed": "bg-green-100 text-green-800 border-green-200",
        "done": "bg-green-100 text-green-800 border-green-200",
        "closed": "bg-green-100 text-green-800 border-green-200",
        "in-progress": "bg-blue-100 text-blue-800 border-blue-200",
        "in progress": "bg-blue-100 text-blue-800 border-blue-200",
        "ongoing": "bg-blue-100 text-blue-800 border-blue-200",
        "pending": "bg-yellow-100 text-yellow-800 border-yellow-200",
        "not started": "bg-yellow-100 text-yellow-800 border-yellow-200",
        "blocked": "bg-red-100 text-red-800 border-red-200",
        "on-hold": "bg-red-100 text-red-800 border-red-200"
    }
    
    status = task.get("status", "pending").lower()
    color_class = status_colors.get(status, "bg-gray-100 text-gray-800 border-gray-200")
    
    return f"""
        <div class="p-4 border rounded-lg {color_class} transition-all hover:shadow-md">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <h4 class="font-medium text-gray-900">{task.get('name', f'Task {index + 1}')}</h4>
                    <p class="text-sm text-gray-600 mt-1">Owner: {task.get('owner', 'Unassigned')}</p>
                    {f'<p class="text-sm text-gray-500 mt-1"><i class="fas fa-calendar mr-1"></i>Due: {task.get("due_date", "No due date")}</p>' if task.get('due_date') else ''}
                </div>
                <span class="px-3 py-1 text-xs font-semibold rounded-full {color_class}">
                    {task.get('status', 'Pending').upper()}
                </span>
            </div>
        </div>
    """

def format_blocker_html(blocker, index):
    """Format blocker as HTML"""
    if not isinstance(blocker, dict):
        return ""
    
    severity_colors = {
        "critical": "bg-red-100 border-red-300 text-red-900",
        "high": "bg-red-50 border-red-200 text-red-800",
        "medium": "bg-orange-50 border-orange-200 text-orange-800",
        "low": "bg-yellow-50 border-yellow-200 text-yellow-800"
    }
    
    severity = blocker.get("severity", "medium").lower()
    color_class = severity_colors.get(severity, "bg-gray-50 border-gray-200 text-gray-800")
    
    icon_map = {
        "critical": "fa-exclamation-circle",
        "high": "fa-exclamation-triangle",
        "medium": "fa-info-circle",
        "low": "fa-check-circle"
    }
    
    icon = icon_map.get(severity, "fa-info-circle")
    
    return f"""
        <div class="p-4 border-2 rounded-lg {color_class} transition-all hover:shadow-lg">
            <div class="flex items-start gap-3">
                <div class="flex-shrink-0 mt-1">
                    <i class="fas {icon} text-lg"></i>
                </div>
                <div class="flex-1">
                    <div class="flex items-start justify-between mb-2">
                        <h4 class="font-semibold text-gray-900">{blocker.get('issue', f'Blocker {index + 1}')}</h4>
                        <span class="px-2 py-1 text-xs font-bold rounded-full {color_class}">
                            {severity.upper()}
                        </span>
                    </div>
                    <p class="text-sm text-gray-700 mt-1"><strong>Owner:</strong> {blocker.get('owner', 'Unassigned')}</p>
                    {f'<p class="text-sm text-gray-600 mt-1"><strong>Impact:</strong> {blocker.get("impact", "Not specified")}</p>' if blocker.get('impact') else ''}
                </div>
            </div>
        </div>
    """

def format_tech_stack_html(tech_item, index):
    """Format tech stack item as HTML"""
    if not isinstance(tech_item, dict):
        tech_name = str(tech_item)
        tech_status = "active"
    else:
        tech_name = tech_item.get('name', f'Tech {index + 1}')
        tech_status = tech_item.get('status', 'active')
    
    status_colors = {
        "active": "bg-green-100 text-green-800 border-green-200",
        "planned": "bg-blue-100 text-blue-800 border-blue-200",
        "deprecated": "bg-red-100 text-red-800 border-red-200"
    }
    
    status = tech_status.lower()
    color_class = status_colors.get(status, "bg-gray-100 text-gray-800 border-gray-200")
    
    return f"""
        <div class="p-4 border-2 rounded-lg hover:shadow-md transition-all {color_class}">
            <div class="flex items-center justify-between">
                <h4 class="font-medium text-gray-900 flex items-center gap-2">
                    <i class="fas fa-code"></i>
                    {tech_name}
                </h4>
                <span class="px-2 py-1 text-xs font-semibold rounded {color_class}">
                    {status.upper()}
                </span>
            </div>
        </div>
    """

def generate_chart_data(project_data):
    """Generate chart data from project data with real insights"""
    
    # Task Status Data
    upcoming_tasks = extract_nested_value(project_data, "operations.task_board_upcoming.value") or []
    ongoing_tasks = extract_nested_value(project_data, "operations.task_board_ongoing.value") or []
    all_tasks = upcoming_tasks + ongoing_tasks
    
    task_status_counts = {
        "Not Started": 0,
        "In Progress": 0,
        "Completed": 0,
        "Blocked": 0
    }
    
    for task in all_tasks:
        if isinstance(task, dict):
            status = task.get("status", "not started").lower()
            if status in ["completed", "done", "closed"]:
                task_status_counts["Completed"] += 1
            elif status in ["in-progress", "ongoing", "started", "in progress"]:
                task_status_counts["In Progress"] += 1
            elif status in ["blocked", "on-hold"]:
                task_status_counts["Blocked"] += 1
            else:
                task_status_counts["Not Started"] += 1
    
    # Blocker Severity Analysis
    blockers = extract_nested_value(project_data, "operations.blockers.value") or []
    blocker_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    
    for blocker in blockers:
        if isinstance(blocker, dict):
            severity = blocker.get("severity", "medium").lower()
            if severity == "critical":
                blocker_counts["Critical"] += 1
            elif severity == "high":
                blocker_counts["High"] += 1
            elif severity == "medium":
                blocker_counts["Medium"] += 1
            elif severity == "low":
                blocker_counts["Low"] += 1
    
    # Tech Stack Distribution
    tech_stack_data = extract_nested_value(project_data, "technical.tech_stack.value") or {}
    tech_distribution = {"Active": 0, "Planned": 0, "Deprecated": 0}
    
    if isinstance(tech_stack_data, dict):
        tech_distribution["Active"] = len(tech_stack_data.get("active", []))
        tech_distribution["Planned"] = len(tech_stack_data.get("planned", []))
        tech_distribution["Deprecated"] = len(tech_stack_data.get("deprecated", []))
    
    # Revenue Channel Analysis
    revenue_channels = extract_nested_value(project_data, "commercial.revenue_channels.value") or []
    channel_labels = []
    channel_data = []
    
    for channel in revenue_channels:
        if isinstance(channel, dict):
            channel_labels.append(channel.get("channel", "Unknown"))
            channel_data.append(channel.get("percentage", 0))
    
    # Invoice Status Analysis
    invoices = extract_nested_value(project_data, "commercial.invoices.value") or []
    invoice_counts = {"Paid": 0, "Pending": 0, "Overdue": 0}
    total_revenue = 0
    monthly_revenue = [0] * 12  # For 12 months
    
    for invoice in invoices:
        if isinstance(invoice, dict):
            amount = invoice.get("amount", 0)
            total_revenue += amount
            status = invoice.get("status", "pending").lower()
            
            if status == "paid":
                invoice_counts["Paid"] += 1
            elif status == "overdue":
                invoice_counts["Overdue"] += 1
            else:
                invoice_counts["Pending"] += 1
            
            # Extract month from due_date for revenue timeline
            due_date = invoice.get("due_date", "")
            if due_date and len(due_date) >= 7:
                try:
                    month = int(due_date.split("-")[1]) - 1
                    if 0 <= month < 12:
                        monthly_revenue[month] += amount
                except:
                    pass
    
    # Stakeholder Sentiment Analysis
    stakeholders = extract_nested_value(project_data, "strategy.stakeholder_map.value") or []
    sentiment_counts = {"Champion": 0, "Supporter": 0, "Neutral": 0, "Detractor": 0}
    influence_counts = {"High": 0, "Medium": 0, "Low": 0}
    
    for stakeholder in stakeholders:
        if isinstance(stakeholder, dict):
            sentiment = stakeholder.get("sentiment", "neutral").lower()
            influence = stakeholder.get("influence", "medium").lower()
            
            if "champion" in sentiment:
                sentiment_counts["Champion"] += 1
            elif "support" in sentiment:
                sentiment_counts["Supporter"] += 1
            elif "detract" in sentiment or "negative" in sentiment:
                sentiment_counts["Detractor"] += 1
            else:
                sentiment_counts["Neutral"] += 1
            
            if influence == "high":
                influence_counts["High"] += 1
            elif influence == "low":
                influence_counts["Low"] += 1
            else:
                influence_counts["Medium"] += 1
    
    # Recent Interactions Timeline
    interactions = extract_nested_value(project_data, "operations.recent_interactions.value") or []
    interaction_types = {"Email": 0, "Meeting": 0, "Call": 0, "Other": 0}
    
    for interaction in interactions[:20]:  # Last 20 interactions
        if isinstance(interaction, dict):
            int_type = interaction.get("type", "other").lower()
            if "email" in int_type:
                interaction_types["Email"] += 1
            elif "meeting" in int_type:
                interaction_types["Meeting"] += 1
            elif "call" in int_type:
                interaction_types["Call"] += 1
            else:
                interaction_types["Other"] += 1
    
    # Project Health Score Components
    traffic_light = extract_nested_value(project_data, "operations.traffic_light.value") or "green"
    engagement_status = extract_nested_value(project_data, "operations.engagement_status.value") or "active"
    
    health_scores = {
        "Task Progress": calculate_completion_rate(all_tasks),
        "Blocker Impact": max(0, 100 - (blocker_counts["Critical"] * 20 + blocker_counts["High"] * 10)),
        "Client Engagement": 85 if engagement_status.lower() != "at_risk" else 40,
        "Revenue Health": min(100, (invoice_counts["Paid"] / max(1, len(invoices))) * 100),
        "Team Capacity": 75  # Could be calculated from actual team data
    }
    
    return {
        "task_status": {
            "labels": list(task_status_counts.keys()),
            "datasets": [{
                "data": list(task_status_counts.values()),
                "backgroundColor": ["#fbbf24", "#3b82f6", "#10b981", "#ef4444"]
            }]
        },
        "blocker_severity": {
            "labels": list(blocker_counts.keys()),
            "datasets": [{
                "data": list(blocker_counts.values()),
                "backgroundColor": ["#dc2626", "#ef4444", "#f97316", "#fbbf24"]
            }]
        },
        "tech_distribution": {
            "labels": list(tech_distribution.keys()),
            "datasets": [{
                "data": list(tech_distribution.values()),
                "backgroundColor": ["#10b981", "#3b82f6", "#ef4444"]
            }]
        },
        "revenue_channels": {
            "labels": channel_labels or ["No Data"],
            "datasets": [{
                "data": channel_data or [100],
                "backgroundColor": ["#8b5cf6", "#06b6d4", "#f59e0b"]
            }]
        },
        "invoice_status": {
            "labels": list(invoice_counts.keys()),
            "datasets": [{
                "data": list(invoice_counts.values()),
                "backgroundColor": ["#10b981", "#f59e0b", "#ef4444"]
            }]
        },
        "revenue_timeline": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "datasets": [{
                "label": "Monthly Revenue",
                "data": monthly_revenue,
                "borderColor": "#10b981",
                "backgroundColor": "rgba(16, 185, 129, 0.1)",
                "fill": True,
                "tension": 0.4
            }]
        },
        "stakeholder_sentiment": {
            "labels": list(sentiment_counts.keys()),
            "datasets": [{
                "data": list(sentiment_counts.values()),
                "backgroundColor": ["#10b981", "#3b82f6", "#fbbf24", "#ef4444"]
            }]
        },
        "stakeholder_influence": {
            "labels": list(influence_counts.keys()),
            "datasets": [{
                "data": list(influence_counts.values()),
                "backgroundColor": ["#dc2626", "#f97316", "#fbbf24"]
            }]
        },
        "interaction_types": {
            "labels": list(interaction_types.keys()),
            "datasets": [{
                "data": list(interaction_types.values()),
                "backgroundColor": ["#3b82f6", "#8b5cf6", "#06b6d4", "#64748b"]
            }]
        },
        "project_health": {
            "labels": list(health_scores.keys()),
            "datasets": [{
                "label": "Health Score",
                "data": list(health_scores.values()),
                "backgroundColor": "rgba(59, 130, 246, 0.2)",
                "borderColor": "#3b82f6",
                "borderWidth": 2,
                "pointBackgroundColor": "#3b82f6",
                "pointBorderColor": "#fff",
                "pointHoverBackgroundColor": "#fff",
                "pointHoverBorderColor": "#3b82f6"
            }]
        }
    }

@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def generate_enhanced_project_report(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive, dynamic HTML report for a specific project.
    Includes all project schema sections with real data, meaningful graphs, and statistics.
    """
    
    # Permission Check
    if current_user.role.lower() not in ["head", "admin", "director", "executive"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Insufficient permissions to generate full project reports."
        )

    db = await get_database()
    
    # Fetch Project & Client
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client = await db.clients.find_one({"client_id": project.get("client_id")})
    client_name = client.get("name") if client else "Unknown Client"
    client_health = client.get("health_score", 100) if client else 100
    
    # Extract all project sections
    universal = project.get("universal_context", {})
    ops = project.get("operations", {})
    tech = project.get("technical", {})
    comm = project.get("commercial", {})
    strat = project.get("strategy", {})
    marketing = project.get("marketing", {})
    other = project.get("other", {})
    
    # Extract traffic light and engagement status
    traffic_light = extract_nested_value(project, "operations.traffic_light.value") or "green"
    engagement_status = extract_nested_value(project, "operations.engagement_status.value") or "Active"
    
    # Calculate metrics using the actual data structure
    upcoming_tasks = extract_nested_value(project, "operations.task_board_upcoming.value") or []
    ongoing_tasks = extract_nested_value(project, "operations.task_board_ongoing.value") or []
    all_tasks = upcoming_tasks + ongoing_tasks
    blockers = extract_nested_value(project, "operations.blockers.value") or []
    
    completed_tasks = sum(1 for task in all_tasks if isinstance(task, dict) and 
                         task.get("status", "").lower() in ["completed", "done", "closed"])
    
    critical_blockers = sum(1 for blocker in blockers if isinstance(blocker, dict) and 
                           blocker.get("severity", "").lower() in ["critical", "high"])
    
    # Calculate revenue from actual data
    invoices = extract_nested_value(project, "commercial.invoices.value") or []
    invoice_revenue = sum(inv.get("amount", 0) for inv in invoices if isinstance(inv, dict))
    
    # Also try to get revenue from financial overview
    financial_overview = extract_nested_value(project, "commercial.financial_overview.value") or {}
    financial_revenue = 0
    if isinstance(financial_overview, dict) and financial_overview.get('total_billed'):
        try:
            # Extract numeric value from strings like "$75,000"
            total_billed_str = financial_overview.get('total_billed', '').replace('$', '').replace(',', '')
            financial_revenue = float(total_billed_str)
        except:
            pass
    
    # Use the maximum of both sources
    total_revenue = max(invoice_revenue, financial_revenue)
    pending_invoices = sum(1 for inv in invoices if isinstance(inv, dict) and 
                          inv.get("status", "").lower() not in ["paid", "completed"])
    paid_invoices = sum(1 for inv in invoices if isinstance(inv, dict) and 
                       inv.get("status", "").lower() in ["paid", "completed"])
    
    # Team size calculation
    team_squad = extract_nested_value(project, "universal_context.squad.value") or []
    stakeholders = extract_nested_value(project, "strategy.stakeholder_map.value") or []
    poc_contacts = extract_nested_value(project, "universal_context.poc_map.value") or []
    
    # Generate chart data
    chart_data = generate_chart_data(project)
    
    # Format content sections using actual data structure
    # Universal Context
    project_summary = extract_nested_value(project, "universal_context.summary.value") or "No project summary available."
    
    timeline_events = extract_nested_value(project, "universal_context.timeline.value") or []
    timeline_html = "".join([
        f"""
        <div class="flex gap-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 hover:shadow-md transition-all">
            <div class="min-w-[120px] text-sm font-bold text-blue-700 flex items-center gap-2">
                <i class="fas fa-calendar-alt"></i>
                {event.get('date', 'TBD')}
            </div>
            <div class="flex-1">
                <p class="text-gray-800 font-medium">{event.get('event', event) if isinstance(event, dict) else event}</p>
                {f'<span class="inline-block mt-1 px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700">{event.get("significance", "Standard")}</span>' if isinstance(event, dict) and event.get('significance') else ''}
            </div>
        </div>
        """ 
        for event in timeline_events[:10]
    ]) if timeline_events else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No timeline events recorded.</p>"
    
    poc_html = "".join([
        f"""
        <div class="p-4 bg-white rounded-lg border-2 border-blue-100 hover:border-blue-300 transition-all hover:shadow-lg">
            <div class="flex items-start justify-between mb-2">
                <h4 class="font-bold text-gray-900 flex items-center gap-2">
                    <i class="fas fa-user-circle text-blue-600"></i>
                    {poc.get('name', 'Unknown')}
                </h4>
                <span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                    {poc.get('influence', 'Unknown')}
                </span>
            </div>
            <p class="text-sm text-gray-600 font-medium">{poc.get('role', 'No role')}</p>
            {f'<p class="text-xs text-gray-500 mt-1"><i class="fas fa-envelope mr-1"></i>{poc.get("email", "")}</p>' if poc.get('email') else ''}
            {f'<span class="inline-block px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 mt-2">{poc.get("sentiment", "Neutral")}</span>' if poc.get('sentiment') else ''}
        </div>
        """ 
        for poc in poc_contacts[:6]
    ]) if poc_contacts else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No POCs defined.</p>"
    
    team_squad_html = "".join([
        f'''<div class="px-3 py-2 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 rounded-full text-sm font-medium border border-blue-200 hover:shadow-md transition-all">
            <i class="fas fa-user mr-1"></i>{member.get("name", member) if isinstance(member, dict) else member}
            {f'<span class="text-xs ml-1 text-blue-600">({member.get("role", "")})</span>' if isinstance(member, dict) and member.get('role') else ''}
        </div>''' 
        for member in team_squad[:15]
    ]) if team_squad else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No team squad defined.</p>"
    
    # Generate critical blockers alert HTML before template replacement
    critical_blockers_alert = ""
    if critical_blockers > 0:
        critical_blockers_alert = f'''
                <div class="mt-6 p-5 bg-gradient-to-r from-red-100 to-orange-100 rounded-xl border-2 border-red-300 shadow-lg">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <i class="fas fa-exclamation-triangle text-3xl text-red-600"></i>
                            <div>
                                <p class="font-bold text-red-900 text-lg">Critical Attention Required</p>
                                <p class="text-sm text-red-700">High-priority blockers need immediate action</p>
                            </div>
                        </div>
                        <span class="text-4xl font-black text-red-600">{critical_blockers}</span>
                    </div>
                </div>
                '''
    
    # Operations content
    upcoming_tasks_html = "".join([format_task_html(task, i) for i, task in enumerate(upcoming_tasks[:10])])
    ongoing_tasks_html = "".join([format_task_html(task, i) for i, task in enumerate(ongoing_tasks[:10])])
    blockers_html = "".join([format_blocker_html(blocker, i) for i, blocker in enumerate(blockers[:10])])
    
    # Recent Interactions
    recent_interactions = extract_nested_value(project, "operations.recent_interactions.value") or []
    interactions_html = "".join([
        f"""
        <div class="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-all">
            <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-semibold text-gray-500">{interaction.get('date', 'Unknown')}</span>
                <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700">
                    <i class="fas {('fa-envelope' if 'email' in interaction.get('type', '').lower() else 'fa-users' if 'meeting' in interaction.get('type', '').lower() else 'fa-phone')} mr-1"></i>
                    {interaction.get('type', 'Unknown')}
                </span>
            </div>
            <p class="text-sm text-gray-700">{interaction.get('summary', interaction)[:150]}...</p>
        </div>
        """ 
        for interaction in recent_interactions[:8]
    ]) if recent_interactions else "<p class='text-gray-400 italic'>No recent interactions recorded.</p>"
    
    # Technical content
    tech_stack_data = extract_nested_value(project, "technical.tech_stack.value") or {}
    tech_stack_html = ""
    if isinstance(tech_stack_data, dict):
        active_tech = tech_stack_data.get("active", [])
        planned_tech = tech_stack_data.get("planned", [])
        deprecated_tech = tech_stack_data.get("deprecated", [])
        
        tech_items = []
        for tech in active_tech[:10]:
            tech_items.append({"name": tech, "status": "active"})
        for tech in planned_tech[:5]:
            tech_items.append({"name": tech, "status": "planned"})
        for tech in deprecated_tech[:3]:
            tech_items.append({"name": tech, "status": "deprecated"})
        
        tech_stack_html = "".join([format_tech_stack_html(tech, i) for i, tech in enumerate(tech_items)])
    
    if not tech_stack_html:
        tech_stack_html = "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No tech stack defined.</p>"
    
    implementation_log = extract_nested_value(project, "technical.implementation_log.value") or []
    impl_html = "".join([
        f'''<div class="p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
            <p class="text-sm text-gray-800">
                <span class="font-bold text-purple-700">{log.get("date", "Unknown")}</span> - 
                <span class="text-gray-700">{log.get("task", log) if isinstance(log, dict) else log}</span>
            </p>
            {f'<p class="text-xs text-gray-600 mt-1">Owner: {log.get("owner", "Unknown")}</p>' if isinstance(log, dict) and log.get('owner') else ''}
        </div>''' 
        for log in implementation_log[:8]
    ]) if implementation_log else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No implementation log entries.</p>"
    
    # Access Credentials
    access_creds = extract_nested_value(project, "technical.access_credentials.value") or []
    access_html = "".join([
        f"""
        <div class="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <h5 class="font-semibold text-gray-900">{cred.get('service', 'Unknown Service')}</h5>
            <p class="text-sm text-gray-600 mt-1"><i class="fas fa-link mr-1"></i>{cred.get('url', 'No URL')}</p>
            <span class="text-xs text-gray-500">{cred.get('access_method', 'Unknown method')}</span>
        </div>
        """ 
        for cred in access_creds[:6]
    ]) if access_creds else "<p class='text-gray-400 italic'>No access credentials available.</p>"
    
    # Commercial content
    active_sow = extract_nested_value(project, "commercial.active_sow.value")
    sow_html = ""
    if active_sow and isinstance(active_sow, dict):
        sow_html = f"""
        <div class="p-6 bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl border-2 border-emerald-300 shadow-lg">
            <div class="flex items-center justify-between mb-4">
                <h4 class="font-bold text-gray-900 text-lg flex items-center gap-2">
                    <i class="fas fa-file-contract text-emerald-600"></i>
                    {active_sow.get('sow_number', 'Unknown SOW')}
                </h4>
                <span class="px-3 py-1 text-sm font-bold rounded-full bg-emerald-200 text-emerald-900">
                    {active_sow.get('status', 'Active')}
                </span>
            </div>
            <div class="grid grid-cols-2 gap-4 mt-3">
                <div>
                    <p class="text-xs text-gray-500">Contract Value</p>
                    <p class="text-lg font-bold text-emerald-700">{active_sow.get('contract_value', 'Not specified')}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-500">Payment Terms</p>
                    <p class="text-sm font-semibold text-gray-700">{active_sow.get('payment_terms', 'Not specified')}</p>
                </div>
            </div>
            {f'<p class="text-sm text-gray-600 mt-3"><i class="fas fa-calendar-alt mr-2"></i>Period: <strong>{active_sow.get("start_date", "")}</strong> to <strong>{active_sow.get("end_date", "")}</strong></p>' if active_sow.get('start_date') else ''}
        </div>
        """
    else:
        sow_html = "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No active contracts.</p>"
    
    financial_overview = extract_nested_value(project, "commercial.financial_overview.value") or {}
    if isinstance(financial_overview, dict):
        financial_text = f"""
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200">
                <p class="text-xs text-gray-600">Total Billed</p>
                <p class="text-2xl font-bold text-green-700">{financial_overview.get('total_billed', '$0')}</p>
            </div>
            <div class="p-4 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg border border-yellow-200">
                <p class="text-xs text-gray-600">Outstanding</p>
                <p class="text-2xl font-bold text-orange-700">{financial_overview.get('outstanding', '$0')}</p>
            </div>
            <div class="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                <p class="text-xs text-gray-600">Monthly Retainer</p>
                <p class="text-2xl font-bold text-blue-700">{financial_overview.get('monthly_retainer', '$0')}</p>
            </div>
        </div>
        """
    else:
        financial_text = "<p class='text-gray-700 p-4 bg-gray-50 rounded-lg'>No financial overview available.</p>"
    
    # Revenue Channels
    revenue_channels = extract_nested_value(project, "commercial.revenue_channels.value") or []
    revenue_channels_html = "".join([
        f"""
        <div class="p-3 bg-purple-50 rounded-lg border border-purple-200">
            <div class="flex items-center justify-between">
                <span class="font-medium text-gray-900">{channel.get('channel', 'Unknown')}</span>
                <span class="text-lg font-bold text-purple-700">{channel.get('percentage', 0)}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div class="bg-purple-600 h-2 rounded-full" style="width: {channel.get('percentage', 0)}%"></div>
            </div>
        </div>
        """ 
        for channel in revenue_channels[:5]
    ]) if revenue_channels else "<p class='text-gray-400 italic'>No revenue channel data available.</p>"
    
    # Strategy content
    stakeholder_html = "".join([
        f"""
        <div class="p-4 bg-white rounded-lg border-2 border-orange-100 hover:border-orange-300 transition-all hover:shadow-lg">
            <div class="flex items-start justify-between mb-2">
                <div>
                    <h4 class="font-bold text-gray-900 flex items-center gap-2">
                        <i class="fas fa-user-tie text-orange-600"></i>
                        {stakeholder.get('name', 'Unknown')}
                    </h4>
                    <p class="text-sm text-gray-600 font-medium">{stakeholder.get('role', 'No role')}</p>
                </div>
                <div class="text-right">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800 block mb-1">
                        {stakeholder.get('influence', 'Unknown')}
                    </span>
                    <span class="px-2 py-1 text-xs font-semibold rounded-full {('bg-green-100 text-green-800' if 'champion' in stakeholder.get('sentiment', '').lower() else 'bg-yellow-100 text-yellow-800' if 'neutral' in stakeholder.get('sentiment', '').lower() else 'bg-red-100 text-red-800')}">
                        {stakeholder.get('sentiment', 'Unknown')}
                    </span>
                </div>
            </div>
        </div>
        """ 
        for stakeholder in stakeholders[:8]
    ]) if stakeholders else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No stakeholders defined.</p>"
    
    goals_roadmap = extract_nested_value(project, "strategy.goals_roadmap.value") or []
    goals_html = "".join([
        f"""
        <div class="p-4 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border-l-4 border-orange-500">
            <div class="flex items-start justify-between mb-2">
                <h5 class="font-bold text-gray-900">{goal.get("goal", goal) if isinstance(goal, dict) else goal}</h5>
                {f'<span class="px-2 py-1 text-xs rounded-full bg-orange-200 text-orange-900">{goal.get("priority", "Standard")}</span>' if isinstance(goal, dict) and goal.get('priority') else ''}
            </div>
            {f'<p class="text-sm text-gray-600"><i class="fas fa-calendar mr-1"></i>Timeline: {goal.get("timeline", "Not specified")}</p>' if isinstance(goal, dict) and goal.get('timeline') else ''}
        </div>
        """ 
        for goal in goals_roadmap[:6]
    ]) if goals_roadmap else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No goals defined.</p>"
    
    upsell_opportunities = extract_nested_value(project, "strategy.upsell_opportunities.value") or []
    upsell_html = "".join([
        f'<div class="p-3 bg-green-50 rounded-lg border border-green-200 hover:shadow-md transition-all"><p class="text-sm text-green-800"><i class="fas fa-lightbulb text-green-600 mr-2"></i>{opp}</p></div>' 
        for opp in upsell_opportunities[:5]
    ]) if upsell_opportunities else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No upsell opportunities identified.</p>"
    
    competitors = extract_nested_value(project, "strategy.competitors.value") or []
    competitors_html = "".join([
        f'<div class="p-3 bg-red-50 rounded-lg border border-red-200"><p class="text-sm text-red-800"><i class="fas fa-trophy text-red-600 mr-2"></i>{comp}</p></div>' 
        for comp in competitors[:5]
    ]) if competitors else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No competitors identified.</p>"
    
    ecosystem = extract_nested_value(project, "strategy.ecosystem.value") or []
    ecosystem_html = "".join([
        f"""
        <div class="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
            <h5 class="font-semibold text-gray-900">{eco.get('platform', 'Unknown')}</h5>
            <p class="text-sm text-gray-600">{eco.get('purpose', 'No purpose specified')}</p>
        </div>
        """ 
        for eco in ecosystem[:6]
    ]) if ecosystem else "<p class='text-gray-400 italic'>No ecosystem data available.</p>"
    
    # Marketing content
    success_stories = extract_nested_value(project, "marketing.success_stories.value") or []
    success_html = "".join([
        f"""
        <div class="p-4 bg-gradient-to-r from-pink-50 to-rose-50 rounded-lg border-2 border-pink-200 hover:shadow-lg transition-all">
            <h5 class="font-bold text-gray-900 flex items-center gap-2">
                <i class="fas fa-star text-pink-600"></i>
                {story.get("title", "Success Story") if isinstance(story, dict) else story}
            </h5>
            {f'<p class="text-sm text-gray-700 mt-2">{story.get("description", "")}</p>' if isinstance(story, dict) and story.get('description') else ''}
        </div>
        """ 
        for story in success_stories[:4]
    ]) if success_stories else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No success stories available.</p>"
    
    feedback = extract_nested_value(project, "other.feedback.value") or []
    feedback_html = "".join([
        f"""
        <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div class="flex items-start gap-3">
                <i class="fas fa-comment-dots text-gray-600 mt-1"></i>
                <div>
                    <p class="font-semibold text-gray-900">{feedback_item.get("from", "Unknown") if isinstance(feedback_item, dict) else "Feedback"}</p>
                    <p class="text-sm text-gray-700 mt-1">{feedback_item.get("feedback", feedback_item) if isinstance(feedback_item, dict) else feedback_item}</p>
                    {f'<span class="inline-block mt-2 px-2 py-1 text-xs rounded-full {("bg-green-100 text-green-800" if "positive" in feedback_item.get("sentiment", "").lower() else "bg-red-100 text-red-800" if "negative" in feedback_item.get("sentiment", "").lower() else "bg-gray-100 text-gray-800")}">{feedback_item.get("sentiment", "Neutral")}</span>' if isinstance(feedback_item, dict) and feedback_item.get('sentiment') else ''}
                </div>
            </div>
        </div>
        """ 
        for feedback_item in feedback[:5]
    ]) if feedback else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No feedback available.</p>"
    
    # Generate HTML using string replacement to avoid format conflicts
    html_content = COMPREHENSIVE_REPORT_TEMPLATE
    html_content = html_content.replace("{project_name}", project.get("name", "Unnamed Project"))
    html_content = html_content.replace("{project_status}", project.get("status", engagement_status))
    html_content = html_content.replace("{status_color}", get_status_color(engagement_status))
    html_content = html_content.replace("{traffic_light}", traffic_light.upper())
    html_content = html_content.replace("{traffic_light_color}", get_traffic_light_color(traffic_light))
    html_content = html_content.replace("{client_name}", client_name)
    html_content = html_content.replace("{generated_date}", datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC"))
    html_content = html_content.replace("{generated_by}", current_user.full_name or current_user.email)
    html_content = html_content.replace("{health_score}", str(client_health))
    
    # Replace metrics
    html_content = html_content.replace("{total_tasks}", str(len(all_tasks)))
    html_content = html_content.replace("{completed_tasks}", str(completed_tasks))
    html_content = html_content.replace("{task_completion_rate}", str(calculate_completion_rate(all_tasks)))
    # Format revenue properly before replacement
    formatted_revenue = f"${total_revenue:,.0f}" if total_revenue > 0 else "$0"
    html_content = html_content.replace("${total_revenue:,.0f}", formatted_revenue)
    html_content = html_content.replace("{total_revenue}", formatted_revenue)
    html_content = html_content.replace("{active_contracts}", str(1 if active_sow else 0))
    html_content = html_content.replace("{team_size}", str(len(team_squad)))
    html_content = html_content.replace("{stakeholder_count}", str(len(stakeholders)))
    html_content = html_content.replace("{total_blockers}", str(len(blockers)))
    html_content = html_content.replace("{critical_blockers}", str(critical_blockers))
    html_content = html_content.replace("{pending_invoices}", str(pending_invoices))
    html_content = html_content.replace("{paid_invoices}", str(paid_invoices))
    html_content = html_content.replace("{total_invoices}", str(len(invoices)))
    
    # Replace task counts
    html_content = html_content.replace("{upcoming_tasks_count}", str(len(upcoming_tasks)))
    html_content = html_content.replace("{ongoing_tasks_count}", str(len(ongoing_tasks)))
    
    # Replace content sections
    html_content = html_content.replace("{project_summary}", project_summary)
    html_content = html_content.replace("{timeline_events}", timeline_html)
    html_content = html_content.replace("{poc_contacts}", poc_html)
    html_content = html_content.replace("{team_squad}", team_squad_html)
    html_content = html_content.replace("{upcoming_tasks}", upcoming_tasks_html if upcoming_tasks_html else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No upcoming tasks.</p>")
    html_content = html_content.replace("{ongoing_tasks}", ongoing_tasks_html if ongoing_tasks_html else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No ongoing tasks.</p>")
    html_content = html_content.replace("{blockers_list}", blockers_html if blockers_html else "<p class='text-gray-400 italic p-4 bg-gray-50 rounded-lg'>No blockers reported.</p>")
    html_content = html_content.replace("{critical_blockers_alert}", critical_blockers_alert)
    html_content = html_content.replace("{recent_interactions}", interactions_html)
    html_content = html_content.replace("{tech_stack_items}", tech_stack_html)
    html_content = html_content.replace("{implementation_log}", impl_html)
    html_content = html_content.replace("{access_credentials}", access_html)
    html_content = html_content.replace("{active_contracts_list}", sow_html)
    html_content = html_content.replace("{financial_overview}", financial_text)
    html_content = html_content.replace("{revenue_channels}", revenue_channels_html)
    html_content = html_content.replace("{stakeholder_map}", stakeholder_html)
    html_content = html_content.replace("{goals_roadmap}", goals_html)
    html_content = html_content.replace("{upsell_opportunities}", upsell_html)
    html_content = html_content.replace("{competitors}", competitors_html)
    html_content = html_content.replace("{ecosystem}", ecosystem_html)
    html_content = html_content.replace("{success_stories}", success_html)
    html_content = html_content.replace("{feedback_section}", feedback_html)
    
    # Replace chart data
    html_content = html_content.replace("{task_status_data}", json.dumps(chart_data["task_status"]))
    html_content = html_content.replace("{blocker_severity_data}", json.dumps(chart_data["blocker_severity"]))
    html_content = html_content.replace("{tech_distribution_data}", json.dumps(chart_data["tech_distribution"]))
    html_content = html_content.replace("{revenue_channels_data}", json.dumps(chart_data["revenue_channels"]))
    html_content = html_content.replace("{invoice_status_data}", json.dumps(chart_data["invoice_status"]))
    html_content = html_content.replace("{revenue_timeline_data}", json.dumps(chart_data["revenue_timeline"]))
    html_content = html_content.replace("{stakeholder_sentiment_data}", json.dumps(chart_data["stakeholder_sentiment"]))
    html_content = html_content.replace("{stakeholder_influence_data}", json.dumps(chart_data["stakeholder_influence"]))
    html_content = html_content.replace("{interaction_types_data}", json.dumps(chart_data["interaction_types"]))
    html_content = html_content.replace("{project_health_data}", json.dumps(chart_data["project_health"]))

    return html_content
COMPREHENSIVE_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Project Report - {project_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        // Tailwind config - using string concatenation to avoid format conflicts
        var tailwindConfig = {{
            "theme": {{
                "extend": {{
                    "fontFamily": {{
                        "sans": ["Inter", "sans-serif"]
                    }},
                    "colors": {{
                        "nexus": {{
                            "50": "#f0f9ff",
                            "100": "#e0f2fe",
                            "200": "#bae6fd",
                            "300": "#7dd3fc",
                            "400": "#38bdf8",
                            "500": "#0ea5e9",
                            "600": "#0284c7",
                            "700": "#0369a1",
                            "800": "#075985",
                            "900": "#0c4a6e",
                            "950": "#082f49"
                        }}
                    }}
                }}
            }}
        }};
        tailwind.config = tailwindConfig;
    </script>
    <style>
        @media print { 
            .no-print { display: none !important; } 
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } 
            .page-break { page-break-before: always; } 
            .avoid-break { page-break-inside: avoid; }
            @page { margin: 1.5cm; }
        }
        body { 
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
            color: #1e293b; 
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        .card { 
            background: white; 
            border-radius: 0.75rem; 
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        .card:hover {
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            border-color: #cbd5e1;
        }
        .metric-card { 
            background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%); 
            border: 1px solid #e2e8f0; 
            transition: all 0.3s ease; 
            position: relative;
            overflow: hidden;
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #0ea5e9 0%, #3b82f6 50%, #8b5cf6 100%);
        }
        .metric-card:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1); 
        }
        .chart-container { 
            position: relative; 
            height: 350px; 
            padding: 1.5rem;
            background: #fafbfc;
            border-radius: 0.5rem;
            border: 1px solid #e2e8f0;
        }
        .progress-bar { 
            background: linear-gradient(90deg, #0ea5e9 0%, #3b82f6 50%, #8b5cf6 100%); 
            border-radius: 9999px; 
            transition: width 0.8s ease; 
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        @keyframes fadeIn { 
            from { opacity: 0; transform: translateY(20px); } 
            to { opacity: 1; transform: translateY(0); } 
        }
        .fade-in { 
            animation: fadeIn 0.8s ease-out; 
        }
        @keyframes pulse { 
            0%, 100% { opacity: 1; } 
            50% { opacity: 0.7; } 
        }
        .pulse { 
            animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite; 
        }
        .gradient-text {
            background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .section-header {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-left: 5px solid #0ea5e9;
            padding: 2rem;
            border-radius: 0.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            border: 1px solid #e2e8f0;
        }
        .professional-gradient {
            background: linear-gradient(135deg, #1e293b 0%, #334155 25%, #475569 50%, #64748b 75%, #94a3b8 100%);
        }
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
        }
        .metric-value {
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.025em;
        }
    </style>
</head>
<body class="antialiased min-h-screen">

    <!-- Floating Actions Bar -->
    <div class="fixed top-6 right-6 z-50 no-print flex gap-4">
        <button onclick="window.print()" class="bg-gradient-to-r from-slate-700 to-slate-900 hover:from-slate-800 hover:to-slate-950 text-white font-bold py-4 px-8 rounded-2xl shadow-2xl flex items-center gap-3 transition-all transform hover:scale-105 border-2 border-white/20 relative z-10">
            <i class="fas fa-print text-lg"></i> 
            <span>Print Report</span>
        </button>
        <button onclick="window.scrollTo(0, 0)" class="bg-white hover:bg-gray-50 text-gray-800 font-bold py-4 px-8 rounded-2xl shadow-xl flex items-center gap-3 transition-all border-2 border-gray-200 hover:border-gray-300">
            <i class="fas fa-arrow-up text-lg"></i> 
            <span>Top</span>
        </button>
    </div>

    <!-- Cover Page -->
    <div class="max-w-7xl mx-auto p-8 pt-20 page-break">
        <div class="text-center py-32 professional-gradient text-white rounded-3xl shadow-2xl mb-12 relative overflow-hidden border border-gray-700">
            <div class="absolute inset-0 opacity-20">
                <div class="absolute transform rotate-45 -translate-x-1/2 -translate-y-1/2 top-1/2 left-1/2 w-96 h-96 bg-white rounded-full blur-3xl"></div>
                <div class="absolute top-0 right-0 w-64 h-64 bg-blue-500 rounded-full blur-3xl opacity-30"></div>
                <div class="absolute bottom-0 left-0 w-80 h-80 bg-purple-500 rounded-full blur-3xl opacity-30"></div>
            </div>
            <div class="relative z-10">
                <div class="inline-block px-8 py-4 bg-white/10 rounded-full text-sm font-semibold backdrop-blur-md border border-white/30 mb-10 shadow-lg">
                    <i class="fas fa-building mr-3"></i>{client_name}
                </div>
                <h1 class="text-8xl font-black mb-10 tracking-tight leading-tight">{project_name}</h1>
                <div class="flex items-center justify-center gap-8 mb-12 flex-wrap max-w-4xl mx-auto">
                    <div class="inline-flex items-center px-8 py-4 bg-white/10 rounded-full backdrop-blur-md border border-white/30 shadow-lg">
                        <span class="status-indicator {status_color}"></span>
                        <span class="font-bold text-white">Status: {project_status}</span>
                    </div>
                    <div class="inline-flex items-center px-8 py-4 bg-white/10 rounded-full backdrop-blur-md border border-white/30 shadow-lg">
                        <span class="status-indicator {traffic_light_color}"></span>
                        <span class="font-bold text-white">Traffic Light: {traffic_light}</span>
                    </div>
                    <div class="inline-flex items-center px-8 py-4 bg-white/10 rounded-full backdrop-blur-md border border-white/30 shadow-lg">
                        <i class="fas fa-chart-line mr-3"></i>
                        <span class="font-bold text-white">Health Score: {health_score}%</span>
                    </div>
                </div>
                <div class="text-slate-200 space-y-3 text-lg">
                    <p><i class="fas fa-calendar-alt mr-3"></i>Generated on {generated_date}</p>
                    <p><i class="fas fa-user mr-3"></i>Generated by {generated_by}</p>
                    <p class="text-sm text-slate-300 mt-4 font-medium">Comprehensive Project Intelligence Report</p>
                </div>
            </div>
        </div>

        <!-- Executive Dashboard -->
        <div class="mb-16">
            <h2 class="text-5xl font-black text-gray-800 mb-12 gradient-text text-center tracking-tight">Executive Dashboard</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 fade-in">
                <div class="metric-card p-8 rounded-2xl">
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl flex items-center justify-center shadow-lg">
                            <i class="fas fa-tasks text-3xl text-blue-600"></i>
                        </div>
                        <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Task Management</span>
                    </div>
                    <div class="text-5xl font-black text-gray-900 mb-2 metric-value">{total_tasks}</div>
                    <div class="text-sm text-gray-600 mb-4 font-medium">{completed_tasks} completed ({task_completion_rate}%)</div>
                    <div class="w-full bg-gray-200 rounded-full h-4 shadow-inner">
                        <div class="progress-bar h-4 shadow-lg" style="width: {task_completion_rate}%"></div>
                    </div>
                    <div class="mt-4 text-xs text-gray-500 font-medium">Completion Rate</div>
                </div>

                <div class="metric-card p-8 rounded-2xl">
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 bg-gradient-to-br from-emerald-50 to-green-100 rounded-2xl flex items-center justify-center shadow-lg">
                            <i class="fas fa-dollar-sign text-3xl text-emerald-600"></i>
                        </div>
                        <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Financial</span>
                    </div>
                    <div class="text-5xl font-black text-gray-900 mb-2 metric-value">${total_revenue:,.0f}</div>
                    <div class="text-sm text-gray-600 mb-4 font-medium">{active_contracts} active contract(s)</div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-gray-500">{paid_invoices}/{total_invoices} invoices paid</span>
                        <span class="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full font-semibold">Revenue</span>
                    </div>
                </div>

                <div class="metric-card p-8 rounded-2xl">
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 bg-gradient-to-br from-purple-50 to-indigo-100 rounded-2xl flex items-center justify-center shadow-lg">
                            <i class="fas fa-users text-3xl text-purple-600"></i>
                        </div>
                        <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Team</span>
                    </div>
                    <div class="text-5xl font-black text-gray-900 mb-2 metric-value">{team_size}</div>
                    <div class="text-sm text-gray-600 mb-4 font-medium">{stakeholder_count} stakeholders</div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-gray-500">Active collaboration</span>
                        <span class="px-2 py-1 bg-purple-100 text-purple-700 rounded-full font-semibold">Personnel</span>
                    </div>
                </div>

                <div class="metric-card p-8 rounded-2xl">
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 bg-gradient-to-br from-red-50 to-orange-100 rounded-2xl flex items-center justify-center shadow-lg">
                            <i class="fas fa-exclamation-triangle text-3xl text-orange-600"></i>
                        </div>
                        <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Risk</span>
                    </div>
                    <div class="text-5xl font-black text-gray-900 mb-2 metric-value">{total_blockers}</div>
                    <div class="text-sm text-red-600 font-semibold mb-4">{critical_blockers} critical</div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-gray-500">Requires attention</span>
                        <span class="px-2 py-1 bg-red-100 text-red-700 rounded-full font-semibold">Blockers</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Key Analytics Overview -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-16 fade-in">
            <div class="card p-10 hover:shadow-2xl transition-all border border-gray-200">
                <h3 class="text-3xl font-bold text-gray-800 mb-8 flex items-center gap-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl flex items-center justify-center">
                        <i class="fas fa-chart-pie text-2xl text-blue-600"></i>
                    </div>
                    Task Status Distribution
                </h3>
                <div class="chart-container">
                    <canvas id="taskStatusChart"></canvas>
                </div>
                <div class="mt-6 text-sm text-gray-600 text-center font-medium">
                    Real-time task completion tracking across all project phases
                </div>
            </div>
            
            <div class="card p-10 hover:shadow-2xl transition-all border border-gray-200">
                <h3 class="text-3xl font-bold text-gray-800 mb-8 flex items-center gap-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-red-50 to-red-100 rounded-xl flex items-center justify-center">
                        <i class="fas fa-heartbeat text-2xl text-red-600"></i>
                    </div>
                    Project Health Radar
                </h3>
                <div class="chart-container">
                    <canvas id="projectHealthChart"></canvas>
                </div>
                <div class="mt-6 text-sm text-gray-600 text-center font-medium">
                    Multi-dimensional health assessment across key performance indicators
                </div>
            </div>

            <div class="card p-10 hover:shadow-2xl transition-all border border-gray-200">
                <h3 class="text-3xl font-bold text-gray-800 mb-8 flex items-center gap-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl flex items-center justify-center">
                        <i class="fas fa-exclamation-circle text-2xl text-orange-600"></i>
                    </div>
                    Blocker Severity Analysis
                </h3>
                <div class="chart-container">
                    <canvas id="blockerSeverityChart"></canvas>
                </div>
                <div class="mt-6 text-sm text-gray-600 text-center font-medium">
                    Critical blocker identification and severity distribution
                </div>
            </div>

            <div class="card p-10 hover:shadow-2xl transition-all border border-gray-200">
                <h3 class="text-3xl font-bold text-gray-800 mb-8 flex items-center gap-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl flex items-center justify-center">
                        <i class="fas fa-comments text-2xl text-blue-600"></i>
                    </div>
                    Communication Patterns
                </h3>
                <div class="chart-container">
                    <canvas id="interactionTypesChart"></canvas>
                </div>
                <div class="mt-6 text-sm text-gray-600 text-center font-medium">
                    Recent interaction frequency by communication channel
                </div>
            </div>
        </div>
    </div>

    <!-- Universal Context Section -->
    <div class="max-w-7xl mx-auto p-8 page-break avoid-break">
        <div class="section-header">
            <h2 class="text-4xl font-black text-gray-800 flex items-center gap-4">
                <div class="w-16 h-16 bg-gradient-to-br from-nexus-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <i class="fas fa-globe text-3xl text-white"></i>
                </div>
                <span class="gradient-text">Universal Context</span>
            </h2>
            <p class="text-gray-600 mt-2 ml-20">Core project information, team structure, and key timeline events</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 space-y-6">
                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
                        <i class="fas fa-file-alt text-blue-600"></i>
                        Project Summary
                    </h3>
                    <div class="prose max-w-none text-gray-700 leading-relaxed">
                        {project_summary}
                    </div>
                </div>

                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-timeline text-blue-600"></i>
                        Key Timeline Events
                    </h3>
                    <div class="space-y-3">
                        {timeline_events}
                    </div>
                </div>
            </div>

            <div class="space-y-6">
                <div class="card p-8 bg-gradient-to-br from-blue-50 to-indigo-50 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-user-circle text-blue-600"></i>
                        Points of Contact
                    </h3>
                    <div class="space-y-4">
                        {poc_contacts}
                    </div>
                </div>

                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-users text-purple-600"></i>
                        Team Squad ({team_size})
                    </h3>
                    <div class="flex flex-wrap gap-2">
                        {team_squad}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Operations Section -->
    <div class="max-w-7xl mx-auto p-8 page-break avoid-break">
        <div class="section-header">
            <h2 class="text-4xl font-black text-gray-800 flex items-center gap-4">
                <div class="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <i class="fas fa-cogs text-3xl text-white"></i>
                </div>
                <span class="gradient-text">Operations Management</span>
            </h2>
            <p class="text-gray-600 mt-2 ml-20">Task tracking, blocker management, and operational insights</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-clipboard-list text-green-600"></i>
                    Task Management
                </h3>
                <div class="space-y-6">
                    <div>
                        <h4 class="font-bold text-gray-600 mb-4 flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-yellow-500"></span>
                            Upcoming Tasks ({upcoming_tasks_count})
                        </h4>
                        <div class="space-y-3 max-h-96 overflow-y-auto">
                            {upcoming_tasks}
                        </div>
                    </div>
                    <div>
                        <h4 class="font-bold text-gray-600 mb-4 flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                            Ongoing Tasks ({ongoing_tasks_count})
                        </h4>
                        <div class="space-y-3 max-h-96 overflow-y-auto">
                            {ongoing_tasks}
                        </div>
                    </div>
                </div>
            </div>

            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-shield-alt text-red-600"></i>
                    Blockers & Issues ({total_blockers})
                </h3>
                <div class="space-y-4 max-h-[600px] overflow-y-auto">
                    {blockers_list}
                </div>
                {critical_blockers_alert}
            </div>
        </div>

        <div class="card p-8 hover:shadow-xl transition-all">
            <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                <i class="fas fa-history text-blue-600"></i>
                Recent Client Interactions
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recent_interactions}
            </div>
        </div>
    </div>

    <!-- Technical Intelligence Section -->
    <div class="max-w-7xl mx-auto p-8 page-break avoid-break">
        <div class="section-header">
            <h2 class="text-4xl font-black text-gray-800 flex items-center gap-4">
                <div class="w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <i class="fas fa-microchip text-3xl text-white"></i>
                </div>
                <span class="gradient-text">Technical Intelligence</span>
            </h2>
            <p class="text-gray-600 mt-2 ml-20">Technology stack, implementation logs, and technical credentials</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 space-y-6">
                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-layer-group text-purple-600"></i>
                        Technology Stack
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {tech_stack_items}
                    </div>
                </div>

                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-code-branch text-purple-600"></i>
                        Implementation Log
                    </h3>
                    <div class="space-y-3 max-h-96 overflow-y-auto">
                        {implementation_log}
                    </div>
                </div>
            </div>

            <div class="space-y-6">
                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-chart-bar text-purple-600"></i>
                        Tech Stack Distribution
                    </h3>
                    <div class="chart-container" style="height: 250px;">
                        <canvas id="techDistributionChart"></canvas>
                    </div>
                </div>

                <div class="card p-8 bg-gradient-to-br from-purple-50 to-indigo-50 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-key text-purple-600"></i>
                        Access Credentials
                    </h3>
                    <div class="space-y-3 max-h-80 overflow-y-auto">
                        {access_credentials}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Commercial Section -->
    <div class="max-w-7xl mx-auto p-8 page-break avoid-break">
        <div class="section-header">
            <h2 class="text-4xl font-black text-gray-800 flex items-center gap-4">
                <div class="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <i class="fas fa-chart-line text-3xl text-white"></i>
                </div>
                <span class="gradient-text">Commercial Overview</span>
            </h2>
            <p class="text-gray-600 mt-2 ml-20">Financial health, revenue tracking, and contract management</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-file-contract text-emerald-600"></i>
                    Active Contracts
                </h3>
                <div class="space-y-4">
                    {active_contracts_list}
                </div>
            </div>

            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-wallet text-emerald-600"></i>
                    Financial Overview
                </h3>
                {financial_overview}
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-chart-area text-green-600"></i>
                    Revenue Timeline
                </h3>
                <div class="chart-container">
                    <canvas id="revenueTimelineChart"></canvas>
                </div>
                <div class="mt-4 text-sm text-gray-600 text-center">
                    Monthly revenue progression and financial trends
                </div>
            </div>

            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-file-invoice-dollar text-green-600"></i>
                    Invoice Status Analysis
                </h3>
                <div class="chart-container">
                    <canvas id="invoiceStatusChart"></canvas>
                </div>
                <div class="mt-4 text-sm text-gray-600 text-center">
                    Current invoice payment status and outstanding amounts
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-stream text-purple-600"></i>
                    Revenue Channels
                </h3>
                <div class="space-y-4">
                    {revenue_channels}
                </div>
            </div>

            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-percentage text-purple-600"></i>
                    Revenue Channel Distribution
                </h3>
                <div class="chart-container" style="height: 300px;">
                    <canvas id="revenueChannelsChart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Strategy Section -->
    <div class="max-w-7xl mx-auto p-8 page-break avoid-break">
        <div class="section-header">
            <h2 class="text-4xl font-black text-gray-800 flex items-center gap-4">
                <div class="w-16 h-16 bg-gradient-to-br from-orange-500 to-amber-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <i class="fas fa-chess text-3xl text-white"></i>
                </div>
                <span class="gradient-text">Strategic Alignment</span>
            </h2>
            <p class="text-gray-600 mt-2 ml-20">Stakeholder management, goals roadmap, and competitive positioning</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 space-y-6">
                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-network-wired text-orange-600"></i>
                        Stakeholder Map ({stakeholder_count})
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {stakeholder_map}
                    </div>
                </div>

                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-bullseye text-orange-600"></i>
                        Goals & Roadmap
                    </h3>
                    <div class="space-y-4">
                        {goals_roadmap}
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="card p-8 bg-gradient-to-br from-green-50 to-emerald-50 hover:shadow-xl transition-all">
                        <h3 class="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                            <i class="fas fa-arrow-trend-up text-green-600"></i>
                            Upsell Opportunities
                        </h3>
                        <div class="space-y-3">
                            {upsell_opportunities}
                        </div>
                    </div>

                    <div class="card p-8 bg-gradient-to-br from-red-50 to-orange-50 hover:shadow-xl transition-all">
                        <h3 class="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                            <i class="fas fa-trophy text-red-600"></i>
                            Competitive Landscape
                        </h3>
                        <div class="space-y-3">
                            {competitors}
                        </div>
                    </div>
                </div>
            </div>

            <div class="space-y-6">
                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-smile text-orange-600"></i>
                        Stakeholder Sentiment
                    </h3>
                    <div class="chart-container" style="height: 250px;">
                        <canvas id="stakeholderSentimentChart"></canvas>
                    </div>
                </div>

                <div class="card p-8 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-star text-orange-600"></i>
                        Stakeholder Influence
                    </h3>
                    <div class="chart-container" style="height: 250px;">
                        <canvas id="stakeholderInfluenceChart"></canvas>
                    </div>
                </div>

                <div class="card p-8 bg-gradient-to-br from-indigo-50 to-purple-50 hover:shadow-xl transition-all">
                    <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                        <i class="fas fa-sitemap text-indigo-600"></i>
                        Ecosystem
                    </h3>
                    <div class="space-y-3">
                        {ecosystem}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Marketing & Feedback Section -->
    <div class="max-w-7xl mx-auto p-8 page-break avoid-break">
        <div class="section-header">
            <h2 class="text-4xl font-black text-gray-800 flex items-center gap-4">
                <div class="w-16 h-16 bg-gradient-to-br from-pink-500 to-rose-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <i class="fas fa-bullhorn text-3xl text-white"></i>
                </div>
                <span class="gradient-text">Marketing & Client Feedback</span>
            </h2>
            <p class="text-gray-600 mt-2 ml-20">Success stories, testimonials, and client feedback analysis</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-trophy text-pink-600"></i>
                    Success Stories & Testimonials
                </h3>
                <div class="space-y-4">
                    {success_stories}
                </div>
            </div>

            <div class="card p-8 hover:shadow-xl transition-all">
                <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
                    <i class="fas fa-comments text-pink-600"></i>
                    Client Feedback
                </h3>
                <div class="space-y-4">
                    {feedback_section}
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="max-w-7xl mx-auto p-8 text-center text-gray-500 text-sm no-print">
        <div class="border-t-2 border-gray-300 pt-8">
            <p class="mb-3 text-lg font-semibold text-gray-700">Project Intelligence Report</p>
            <p class="mb-4 text-gray-600">This comprehensive report was automatically generated by the Project Intelligence System</p>
            <div class="inline-block px-6 py-3 bg-red-50 border border-red-200 rounded-lg mb-4">
                <p class="font-bold text-red-800 text-base">Confidential & Proprietary Information</p>
                <p class="text-sm text-red-600 mt-1">This document contains sensitive business information and is intended for authorized personnel only</p>
            </div>
            <div class="mt-6 text-xs text-gray-400">
                <p class="mb-1">© 2026 Project Intelligence System. All rights reserved.</p>
                <p>This report is based on data available as of {generated_date}</p>
            </div>
        </div>
    </div>

    <script>
        // Chart.js Global Configuration
        Chart.defaults.font.family = 'Inter, sans-serif';
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#475569';
        
        // Common chart options
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: {
                            size: 11,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: 'bold' },
                    bodyFont: { size: 12 },
                    cornerRadius: 8
                }
            }
        };

        // Task Status Chart
        new Chart(document.getElementById('taskStatusChart'), {
            type: 'doughnut',
            data: {task_status_data},
            options: {
                ...commonOptions,
                cutout: '65%',
                plugins: {
                    ...commonOptions.plugins,
                    legend: { position: 'right' }
                }
            }
        });

        // Project Health Radar Chart
        new Chart(document.getElementById('projectHealthChart'), {
            type: 'radar',
            data: {project_health_data},
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    legend: { display: false }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            font: { size: 10 }
                        },
                        pointLabels: {
                            font: { size: 11, weight: '600' }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });

        // Blocker Severity Chart
        new Chart(document.getElementById('blockerSeverityChart'), {
            type: 'polarArea',
            data: {blocker_severity_data},
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    legend: { position: 'right' }
                }
            }
        });

        // Interaction Types Chart
        new Chart(document.getElementById('interactionTypesChart'), {
            type: 'doughnut',
            data: {interaction_types_data},
            options: {
                ...commonOptions,
                cutout: '60%'
            }
        });

        // Tech Distribution Chart
        new Chart(document.getElementById('techDistributionChart'), {
            type: 'pie',
            data: {tech_distribution_data},
            options: commonOptions
        });

        // Revenue Timeline Chart
        new Chart(document.getElementById('revenueTimelineChart'), {
            type: 'line',
            data: {revenue_timeline_data},
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        // Invoice Status Chart
        new Chart(document.getElementById('invoiceStatusChart'), {
            type: 'doughnut',
            data: {invoice_status_data},
            options: {
                ...commonOptions,
                cutout: '65%'
            }
        });

        // Revenue Channels Chart
        new Chart(document.getElementById('revenueChannelsChart'), {
            type: 'pie',
            data: {revenue_channels_data},
            options: commonOptions
        });

        // Stakeholder Sentiment Chart
        new Chart(document.getElementById('stakeholderSentimentChart'), {
            type: 'doughnut',
            data: {stakeholder_sentiment_data},
            options: {
                ...commonOptions,
                cutout: '60%'
            }
        });

        // Stakeholder Influence Chart
        new Chart(document.getElementById('stakeholderInfluenceChart'), {
            type: 'pie',
            data: {stakeholder_influence_data},
            options: commonOptions
        });
    </script>
</body>
</html>
"""