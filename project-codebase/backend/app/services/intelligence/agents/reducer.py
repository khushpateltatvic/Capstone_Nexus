from typing import Dict, List, Any
import logging
from datetime import datetime
from app.core.database import get_database
from app.models.domain.project import Project

class Reducer:
    async def reduce_and_persist(self, state: Dict[str, Any]):
        """
        Production-grade Reducer:
        - Deeply merges ALL agent outputs into MongoDB Project documents.
        - Captures all 30+ fields across 7 sections.
        - De-duplicates lists and tracks data lineage.
        """
        logging.info(f"Starting deep reduction and persistence... (State type: {type(state)})")
        
        # 1. Extract context
        if isinstance(state, list):
            logging.warning("State is a list! Using last element.")
            if state and isinstance(state[-1], dict):
                state = state[-1]
            else:
                raise ValueError(f"State is a list but last element is not a dict: {state}")

        metadata = state.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        client_id = metadata.get("client_id", "unknown_client")
        project_id = metadata.get("project_id", "default_project")
        filename = metadata.get("filename", "unknown_source")
        
        # Helper to safely extract dict from potentially list-wrapped output
        def safe_get(key: str) -> Dict[str, Any]:
            val = state.get(key)
            if isinstance(val, list):
                val = val[-1] if val else {}
            return val if isinstance(val, dict) else {}
        
        # Helper to safely iterate over a list, filtering out non-dict elements
        def safe_list(data: Any) -> List[Dict[str, Any]]:
            if not isinstance(data, list):
                return []
            return [item for item in data if isinstance(item, dict)]
        
        # Helper for any list (including strings)
        def any_list(data: Any) -> List[Any]:
            if not isinstance(data, list):
                return []
            return data

        # 2. Gather all agent outputs
        historian = safe_get("historian_output")
        pm = safe_get("pm_output")
        auditor = safe_get("auditor_output")
        tech = safe_get("tech_lead_output")
        strategist = safe_get("strategist_output")
        
        database = await get_database()
        
        # 3. Pull existing document to perform merge
        project_doc = await database.projects.find_one({
            "client_id": client_id,
            "project_id": project_id
        })
        
        # 4. Handle initial creation or missing fields
        if not project_doc:
            project_obj = Project(project_id=project_id, client_id=client_id, name=project_id)
            project_doc = project_obj.dict()
            await database.projects.insert_one(project_doc)

        update_ops = {
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        if not project_doc.get("created_at"):
            update_ops["created_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        def create_datapoint(value: Any, confidence: float = 1.0):
            return {
                "value": value,
                "source_doc": filename,
                "confidence": confidence,
                "timestamp": datetime.utcnow()
            }

        # ========================================
        # SECTION 1: UNIVERSAL CONTEXT (Historian)
        # ========================================
        
        # 1.0 Project Name (First priority)
        if historian.get("project_name"):
            update_ops["name"] = historian["project_name"]
        
        # 1.1 Account Summary
        if historian.get("account_summary"):
            summary = historian["account_summary"]
            update_ops["universal_context.summary"] = create_datapoint(summary)
            # Fallback for name: if project name is still the ID and we don't have project_name
            if "name" not in update_ops and (project_doc.get("name") == project_id or not project_doc.get("name")):
                if len(summary) < 100:
                    update_ops["name"] = summary
        
        # 1.2 Timeline
        if "timeline_events" in historian:
            events = safe_list(historian.get("timeline_events"))
            if events:
                existing = safe_list((project_doc.get("universal_context") or {}).get("timeline", []))
                combined = existing + [e for e in events if e not in existing]
                update_ops["universal_context.timeline"] = create_datapoint(combined)
        
        # 1.3 Engagement Type
        if historian.get("engagement_type"):
            update_ops["universal_context.engagement_type"] = create_datapoint(historian["engagement_type"])
        
        # 1.4 Client Profile
        if historian.get("client_profile"):
            update_ops["universal_context.client_profile"] = create_datapoint(historian["client_profile"])
            # Bridge to Client Model health score
            cp = historian["client_profile"]
            if isinstance(cp, dict) and cp.get("health_score"):
                score_str = cp.get("health_score")
                # Map Excellent/Good/At-Risk/Poor to numeric if needed, or just update metadata
                # Assuming client collection health_score is float (0-100)
                score_map = {"Excellent": 95, "Good": 85, "At-Risk": 60, "Poor": 30}
                numeric_score = score_map.get(score_str)
                if numeric_score:
                    await database.clients.update_one(
                        {"client_id": client_id},
                        {"$set": {"health_score": numeric_score}}
                    )        
        # 1.5 Internal Squad
        if "internal_squad" in historian:
            squad = safe_list(historian.get("internal_squad"))
            if squad:
                existing = safe_list((project_doc.get("universal_context") or {}).get("squad", []))
                squad_dict = {s.get("name"): s for s in existing}
                for s in squad:
                    if s.get("name"):
                        squad_dict[s["name"]] = s
                update_ops["universal_context.squad"] = create_datapoint(list(squad_dict.values()))
        
        # 1.6 POC Map
        if "poc_updates" in historian:
            new_pocs = safe_list(historian.get("poc_updates"))
            if new_pocs:
                existing_val = (project_doc.get("universal_context") or {}).get("poc_map", {})
                existing_pocs = safe_list(existing_val.get("value") if isinstance(existing_val, dict) else [])
                poc_dict = {p.get("name"): p for p in existing_pocs if p.get("name")}
                for p in new_pocs:
                    if p.get("name"):
                        poc_dict[p["name"]] = p
                update_ops["universal_context.poc_map"] = create_datapoint(list(poc_dict.values()))
        
        # Also get POCs from PM (stakeholder interactions)
        if "stakeholder_map" in strategist:
            stakeholders = safe_list(strategist.get("stakeholder_map"))
            if stakeholders:
                existing_val = (project_doc.get("universal_context") or {}).get("poc_map", {})
                existing_pocs = safe_list(existing_val.get("value") if isinstance(existing_val, dict) else [])
                poc_dict = {p.get("name"): p for p in existing_pocs if p.get("name")}
                for s in stakeholders:
                    if s.get("name"):
                        poc_dict[s["name"]] = s
                update_ops["universal_context.poc_map"] = create_datapoint(list(poc_dict.values()))
        
        # 1.7 Communication Hygiene
        if historian.get("communication_hygiene"):
            update_ops["universal_context.communication_hygiene"] = create_datapoint(historian["communication_hygiene"])
        
        # 1.8 Important Notes
        if "important_notes" in historian:
            notes = any_list(historian.get("important_notes"))
            if notes:
                existing = any_list((project_doc.get("universal_context") or {}).get("important_notes", []))
                combined = existing + [n for n in notes if n not in existing]
                update_ops["universal_context.important_notes"] = create_datapoint(combined)
        
        # 1.9 Google Workspace
        if "google_workspace" in historian:
            ws = any_list(historian.get("google_workspace"))
            if ws:
                existing = any_list((project_doc.get("universal_context") or {}).get("google_workspace", []))
                # Manual dedup for strings
                combined = existing + [w for w in ws if w not in existing]
                update_ops["universal_context.google_workspace"] = create_datapoint(combined)

        # ========================================
        # SECTION 2: OPERATIONS (PM)
        # ========================================
        
        # 2.1 Traffic Light
        traffic_light = pm.get("traffic_light", "Green")
        blockers = safe_list(pm.get("blockers"))
        health_score = historian.get("health_score", "Good")
        if health_score == "Poor" or health_score == "At-Risk" or len(blockers) > 0:
            if health_score == "Poor" or any(b.get("severity") == "Critical" for b in blockers):
                traffic_light = "Red"
            else:
                traffic_light = "Yellow"
        
        update_ops["operations.traffic_light"] = create_datapoint(traffic_light)
        
        # 2.2 Task Boards
        if "task_board_upcoming" in pm:
            tasks = safe_list(pm.get("task_board_upcoming"))
            if tasks:
                existing_val = (project_doc.get("operations") or {}).get("task_board_upcoming", {})
                existing = safe_list(existing_val.get("value") if isinstance(existing_val, dict) else [])
                task_dict = {t.get("name"): t for t in existing if t.get("name")}
                for t in tasks:
                    if t.get("name"):
                        task_dict[t["name"]] = t
                update_ops["operations.task_board_upcoming"] = create_datapoint(list(task_dict.values()))
        
        if "task_board_ongoing" in pm:
            tasks = safe_list(pm.get("task_board_ongoing"))
            if tasks:
                existing_val = (project_doc.get("operations") or {}).get("task_board_ongoing", {})
                existing = safe_list(existing_val.get("value") if isinstance(existing_val, dict) else [])
                task_dict = {t.get("name"): t for t in existing if t.get("name")}
                for t in tasks:
                    if t.get("name"):
                        task_dict[t["name"]] = t
                update_ops["operations.task_board_ongoing"] = create_datapoint(list(task_dict.values()))
        
        if "task_board_completed" in pm:
            tasks = safe_list(pm.get("task_board_completed"))
            if tasks:
                existing_val = (project_doc.get("operations") or {}).get("task_board_completed", {})
                existing = safe_list(existing_val.get("value") if isinstance(existing_val, dict) else [])
                task_dict = {t.get("name"): t for t in existing if t.get("name")}
                for t in tasks:
                    if t.get("name"):
                        task_dict[t["name"]] = t
                update_ops["operations.task_board_completed"] = create_datapoint(list(task_dict.values()))
        
        # Legacy task formats
        if "new_tasks" in pm:
            tasks = safe_list(pm.get("new_tasks"))
            if tasks:
                update_ops["operations.task_board_upcoming"] = create_datapoint(tasks)
        
        # 2.3 Blockers
        if blockers:
            update_ops["operations.blockers"] = create_datapoint(blockers)
        
        # 2.4 Recent Interactions
        if "recent_interactions" in pm:
            interactions = safe_list(pm.get("recent_interactions"))
            if interactions:
                existing = safe_list((project_doc.get("operations") or {}).get("recent_interactions", []))
                combined = existing + interactions
                update_ops["operations.recent_interactions"] = create_datapoint(combined[-20:])  # Keep last 20
        
        # 2.5 Engagement Status
        if pm.get("engagement_status"):
            update_ops["operations.engagement_status"] = create_datapoint(pm["engagement_status"])

        # ========================================
        # SECTION 3: TECHNICAL (Tech Lead)
        # ========================================
        
        # 3.1 Tech Stack Matrix
        if "tech_stack_updates" in tech:
            raw_stack = tech["tech_stack_updates"]
            if isinstance(raw_stack, dict):
                active = any_list(raw_stack.get("active", []))
                planned = any_list(raw_stack.get("planned", []))
                deprecated = any_list(raw_stack.get("deprecated", []))
                # Also check old format
                current = any_list(raw_stack.get("current", []))
                added = any_list(raw_stack.get("added", []))
                
                combined_active = list(set(active + current + added))
                
                stack_matrix = {
                    "active": combined_active if combined_active else active,
                    "planned": planned,
                    "deprecated": deprecated
                }
                update_ops["technical.tech_stack"] = create_datapoint(stack_matrix)
            else:
                update_ops["technical.tech_stack"] = create_datapoint(raw_stack)
        
        # 3.2 Access Credentials
        if "access_credentials" in tech:
            creds = safe_list(tech.get("access_credentials"))
            if creds:
                existing = safe_list((project_doc.get("technical") or {}).get("access_credentials", []))
                cred_dict = {c.get("service"): c for c in existing if c.get("service")}
                for c in creds:
                    if c.get("service"):
                        cred_dict[c["service"]] = c
                update_ops["technical.access_credentials"] = create_datapoint(list(cred_dict.values()))
        
        # 3.3 Implementation Log
        if "implementation_log" in tech:
            logs = safe_list(tech.get("implementation_log"))
            if logs:
                existing = safe_list((project_doc.get("technical") or {}).get("implementation_log", []))
                combined = existing + logs
                update_ops["technical.implementation_log"] = create_datapoint(combined)
        
        # 3.4 Experiment Results
        if "experiment_results" in tech:
            experiments = safe_list(tech.get("experiment_results"))
            if experiments:
                existing = safe_list((project_doc.get("technical") or {}).get("experiment_results", []))
                exp_dict = {e.get("name"): e for e in existing if e.get("name")}
                for e in experiments:
                    if e.get("name"):
                        exp_dict[e["name"]] = e
                update_ops["technical.experiment_results"] = create_datapoint(list(exp_dict.values()))

        # ========================================
        # SECTION 4: COMMERCIAL (Auditor)
        # ========================================
        
        # 4.1 Active SOW
        if "sow_data" in auditor:
            sow = auditor["sow_data"]
            if isinstance(sow, dict) and sow.get("contract_value"):
                update_ops["commercial.active_sow"] = create_datapoint(sow, auditor.get("confidence", 1.0))
        
        # 4.2 Financial Overview
        if "financial_overview" in auditor:
            update_ops["commercial.financial_overview"] = create_datapoint(auditor["financial_overview"])
        
        # 4.3 Invoices
        if "invoices" in auditor:
            invoices = safe_list(auditor.get("invoices"))
            if invoices:
                existing = safe_list((project_doc.get("commercial") or {}).get("invoices", []))
                inv_dict = {i.get("invoice_number"): i for i in existing if i.get("invoice_number")}
                for i in invoices:
                    if i.get("invoice_number"):
                        inv_dict[i["invoice_number"]] = i
                update_ops["commercial.invoices"] = create_datapoint(list(inv_dict.values()))
        
        # 4.4 Upcoming Renewals (handle variants)
        renewals_data = auditor.get("upcoming_renewals") or auditor.get("upcoming_legal_renewals")
        if renewals_data:
            update_ops["commercial.upcoming_renewals"] = create_datapoint(renewals_data)
        
        # 4.5 Revenue Channels
        if "revenue_channels" in auditor:
            channels = safe_list(auditor.get("revenue_channels"))
            if channels:
                update_ops["commercial.revenue_channels"] = create_datapoint(channels)

        # ========================================
        # SECTION 5: STRATEGY (Strategist)
        # ========================================
        
        # 5.1 Stakeholder Map
        if "stakeholder_map" in strategist:
            stakeholders = safe_list(strategist.get("stakeholder_map"))
            if stakeholders:
                existing = safe_list((project_doc.get("strategy") or {}).get("stakeholder_map", []))
                sm_dict = {s.get("name"): s for s in existing if s.get("name")}
                for s in stakeholders:
                    if s.get("name"):
                        sm_dict[s["name"]] = s
                update_ops["strategy.stakeholder_map"] = create_datapoint(list(sm_dict.values()))
        
        # 5.2 Stakeholder Hierarchy
        if strategist.get("stakeholder_hierarchy"):
            update_ops["strategy.stakeholder_hierarchy"] = create_datapoint(strategist["stakeholder_hierarchy"])
        
        # 5.3 Goals Roadmap (handles both "goals" and "goals_roadmap" keys)
        goals_data = strategist.get("goals_roadmap") or strategist.get("goals")
        if goals_data:
            goals = safe_list(goals_data)
            if goals:
                existing_val = (project_doc.get("strategy") or {}).get("goals_roadmap", {})
                existing = safe_list(existing_val.get("value") if isinstance(existing_val, dict) else [])
                combined = existing + [g for g in goals if g not in existing]
                update_ops["strategy.goals_roadmap"] = create_datapoint(combined)
            
            # Logic to extract 'name' from goals if not already set
            if not project_doc.get("name") or project_doc.get("name") == project_id:
                for goal in goals:
                    if "For project" in goal.get("goal") or "Project:" in goal.get("goal"):
                        update_ops["name"] = goal["goal"].split(":")[-1].strip()
                        break
        
        # 5.4 Upsell Opportunities
        if "upsell_opportunities" in strategist:
            upsells = safe_list(strategist.get("upsell_opportunities"))
            if upsells:
                existing = safe_list((project_doc.get("strategy") or {}).get("upsell_opportunities", []))
                up_dict = {u.get("opportunity"): u for u in existing if u.get("opportunity")}
                for u in upsells:
                    if u.get("opportunity"):
                        up_dict[u["opportunity"]] = u
                update_ops["strategy.upsell_opportunities"] = create_datapoint(list(up_dict.values()))
        
        # 5.5 Competitors
        if "competitors" in strategist:
            competitors = strategist.get("competitors")
            if isinstance(competitors, list):
                # Could be list of dicts or list of strings
                update_ops["strategy.competitors"] = create_datapoint(competitors)
        
        # 5.6 Ecosystem
        if "ecosystem" in strategist:
            ecosystem = safe_list(strategist.get("ecosystem"))
            if ecosystem:
                update_ops["strategy.ecosystem"] = create_datapoint(ecosystem)

        # ========================================
        # SECTION 6: MARKETING (Strategist)
        # ========================================
        
        # 6.1 Brand Guidelines (handles both "brand_updates" and "brand_guidelines" keys)
        brand_data = strategist.get("brand_guidelines") or strategist.get("brand_updates")
        if brand_data:
            update_ops["marketing.brand_guidelines"] = create_datapoint(brand_data)
        
        # 6.2 Success Stories
        if "success_stories" in strategist:
            stories = safe_list(strategist.get("success_stories"))
            if stories:
                update_ops["marketing.success_stories"] = create_datapoint(stories)
        
        # 6.3 Testimonials
        if "testimonials" in strategist:
            testimonials = safe_list(strategist.get("testimonials"))
            if testimonials:
                update_ops["marketing.testimonials"] = create_datapoint(testimonials)
        
        # 6.4 Public References
        if "public_references" in strategist:
            refs = safe_list(strategist.get("public_references"))
            if refs:
                update_ops["marketing.public_references"] = create_datapoint(refs)

        # ========================================
        # SECTION 7: OTHER
        # ========================================
        
        # 7.1 Feedback
        if "feedback" in pm:
            feedback = safe_list(pm.get("feedback"))
            if feedback:
                existing = safe_list((project_doc.get("other") or {}).get("feedback", []))
                combined = existing + feedback
                update_ops["other.feedback"] = create_datapoint(combined[-50:])  # Keep last 50
        
        # 7.2 Subscriptions (from goals)
        # Already handled in goals_roadmap
        
        # 7.3 Document References
        if "document_references" in strategist:
            docs = any_list(strategist.get("document_references"))
            if docs:
                existing = any_list((project_doc.get("other") or {}).get("document_references", []))
                # Manual dedup for strings
                combined = existing + [d for d in docs if d not in existing]
                update_ops["other.document_references"] = create_datapoint(combined)
        
        # 7.4 Additional Emails
        if "additional_emails" in strategist:
            emails = any_list(strategist.get("additional_emails"))
            if emails:
                existing = any_list((project_doc.get("other") or {}).get("additional_emails", []))
                # Manual dedup for strings
                combined = existing + [e for e in emails if e not in existing]
                update_ops["other.additional_emails"] = create_datapoint(combined)

        # ========================================
        # FINAL UPDATE
        # ========================================
        
        if update_ops:
            logging.info(f"Final update_ops keys for {project_id}: {list(update_ops.keys())}")
            await database.projects.update_one(
                {"client_id": client_id, "project_id": project_id},
                {"$set": update_ops}
            )
            logging.info(f"Updated {len(update_ops)} fields for project {project_id}")
            
        # ========================================
        # POST-PROCESS: Auto-Access for Squad
        # ========================================
        if "internal_squad" in historian:
            squad_emails = set()
            for member in safe_list(historian.get("internal_squad")):
                if member.get("email"):
                    squad_emails.add(member["email"])
            
            if squad_emails:
                # Filter for only users that actually exist in the system
                existing_users = await database.users.find(
                    {"email": {"$in": list(squad_emails)}},
                    {"email": 1}
                ).to_list(length=100)
                
                valid_emails = [u["email"] for u in existing_users]
                
                if valid_emails:
                    await database.projects.update_one(
                        {"client_id": client_id, "project_id": project_id},
                        {"$addToSet": {"access.assigned_users": {"$each": valid_emails}}}
                    )
                    logging.info(f"Auto-granted access to {len(valid_emails)} existing users found in squad")

        # Audit Logging
        await database.metadata.insert_one({
            "event": "production_reduction_complete", 
            "project_id": project_id,
            "client_id": client_id,
            "source_doc": filename,
            "timestamp": datetime.utcnow(),
            "fields_updated": list(update_ops.keys())
        })
        
        return {"status": "success", "project_id": project_id, "fields_updated": len(update_ops)}

reducer = Reducer()
