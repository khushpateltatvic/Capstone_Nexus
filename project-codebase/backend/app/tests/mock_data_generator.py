import random
from typing import List, Dict
from datetime import datetime, timedelta

class MockDataGenerator:
    """
    Generates comprehensive project documents for full pipeline testing.
    Each document is designed to trigger specific agents and extract ALL data fields.
    """
    
    @staticmethod
    def generate_account_overview(client_name: str, project_id: str) -> str:
        """
        Universal Context document - triggers Historian for account summary, timeline, squad, engagement type
        """
        start_date = datetime(2023, 6, 15)
        return f"""
ACCOUNT OVERVIEW: {client_name}
==============================
Document Type: Account Summary
Last Updated: {datetime.now().strftime('%Y-%m-%d')}

1. ACCOUNT SUMMARY
------------------
{client_name} is a mid-market B2B SaaS company in the Financial Technology industry.
They specialize in payment processing and digital banking solutions.
The engagement began on {start_date.strftime('%Y-%m-%d')} as a strategic digital transformation initiative.
Current Health Score: EXCELLENT - Strong partnership with clear roadmap.

2. ENGAGEMENT TYPE
------------------
Type: FTE Model (Fixed Team Engagement)
Billing: Monthly retainer with milestone bonuses
Contract Model: 12-month renewable commitment

3. TIMELINE OF ENGAGEMENT
-------------------------
- {start_date.strftime('%Y-%m-%d')}: Initial discovery call with {client_name}
- {(start_date + timedelta(days=30)).strftime('%Y-%m-%d')}: SOW signed and kickoff meeting
- {(start_date + timedelta(days=60)).strftime('%Y-%m-%d')}: MVP delivered to staging
- {(start_date + timedelta(days=120)).strftime('%Y-%m-%d')}: Production go-live achieved
- {(start_date + timedelta(days=180)).strftime('%Y-%m-%d')}: Phase 2 expansion approved
- {(start_date + timedelta(days=365)).strftime('%Y-%m-%d')}: Contract renewed for Year 2

4. INTERNAL SQUAD (Our Team)
----------------------------
- Alice Chen: Project Manager (PM) - alice.chen@ourcompany.com
- Bob Martinez: Tech Lead - bob.martinez@ourcompany.com  
- Carol Davis: Senior Developer - carol.davis@ourcompany.com
- David Lee: DevOps Engineer - david.lee@ourcompany.com
- Emily Wong: QA Lead - emily.wong@ourcompany.com

5. GOOGLE WORKSPACE TEAM
------------------------
- pm-team@ourcompany.com (Project Management)
- dev-team@ourcompany.com (Development)
- qa-team@ourcompany.com (Quality Assurance)

6. COMMUNICATION HYGIENE
------------------------
Last Email: {(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')} (Alice to John re: Sprint Review)
Last Meeting: {(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')} (Weekly Sync)
Average Response Time: 4 hours
Meeting Frequency: Weekly (Mondays 10am)
Slack Channel: #{client_name.lower().replace(' ', '-')}-project

7. IMPORTANT NOTES
------------------
- Client prefers async communication over meetings
- John (VP Eng) is on PTO from June 1-15
- Budget approval required for any scope changes over $5000
- Security audit scheduled for Q3
"""

    @staticmethod
    def generate_meeting_notes(client_name: str, project_id: str) -> str:
        """
        Operations document - POCs, tasks, blockers, interactions
        """
        return f"""
MEETING NOTES - {client_name} Weekly Sync
==========================================
Date: {datetime.now().strftime('%Y-%m-%d')}
Time: 10:00 AM - 11:00 AM
Project: {project_id}
Type: Weekly Status Meeting

ATTENDEES (POC MAP):
--------------------
From Client ({client_name}):
- John Smith (VP of Engineering) - john.smith@{client_name.lower().replace(' ', '')}.com
  Role: FINAL_DECISION_MAKER, Sentiment: CHAMPION, Very supportive of the project
  
- Sarah Johnson (Product Owner) - sarah.johnson@{client_name.lower().replace(' ', '')}.com
  Role: OPERATIONAL_SUPPORTER, Sentiment: SUPPORTER, Manages day-to-day requirements
  
- Mike Williams (CTO) - mike.williams@{client_name.lower().replace(' ', '')}.com
  Role: BUDGET_CONTROLLER, Sentiment: NEUTRAL, Focused on ROI, needs convincing on Phase 3
  
- Lisa Brown (Security Lead) - lisa.brown@{client_name.lower().replace(' ', '')}.com
  Role: INFLUENCER, Sentiment: SKEPTIC, Has concerns about cloud security

From Our Team:
- Alice Chen (Project Manager)
- Bob Martinez (Tech Lead)

STAKEHOLDER HIERARCHY:
----------------------
Mike Williams (CTO)
├── John Smith (VP Engineering)
│   ├── Sarah Johnson (Product Owner)
│   └── Lisa Brown (Security Lead)

PROJECT STATUS: YELLOW (At Risk)
Traffic Light: YELLOW - Schedule risk due to delayed credentials

TASK UPDATES:
-------------
ONGOING TASKS:
- React Dashboard Migration: 75% complete, Bob leading
- API Performance Optimization: Started this sprint, Carol working on it
- Security Audit Prep: Lisa reviewing documentation

UPCOMING TASKS:
- Mobile App Development: Scheduled for Q3
- Database Migration to Aurora: Planning phase
- Load Testing: Blocked on staging environment

BLOCKERS (CRITICAL):
-------------------
1. CRITICAL: AWS Credentials pending from {client_name} IT team for 2 weeks
   Owner: John Smith | Severity: High | Impact: Blocking deployment
   
2. HIGH: Database migration script needs {client_name} DBA sign-off
   Owner: Lisa Brown | Severity: Medium | Impact: Delaying Phase 2
   
3. MEDIUM: Third-party API rate limits causing staging issues
   Owner: Bob Martinez | Severity: Low | Impact: Test automation affected

RECENT INTERACTIONS:
-------------------
- {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}: Email from Sarah re: new feature request
- {(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')}: Slack DM from John approving scope change
- {(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')}: Video call with Lisa on security requirements
- {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}: Sprint demo to stakeholders

ENGAGEMENT STATUS: ACTIVE_DELIVERY
Currently in active development phase with regular weekly syncs.

FEEDBACK FROM CLIENT:
---------------------
John said: "The team has been incredibly responsive. Really impressed with the progress on the dashboard."
Sarah mentioned: "Would love to see better documentation for the new APIs."
Mike asked: "Can we get a cost breakdown for the Q3 expansion proposal?"

NEXT MEETING: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')} at 10:00 AM
"""

    @staticmethod
    def generate_sow_content(client_name: str, project_id: str) -> str:
        """
        Commercial document - SOW, financials, renewals
        """
        contract_value = random.randint(150000, 350000)
        monthly_retainer = random.randint(12000, 30000)
        sow_number = f"SOW-2024-{random.randint(100, 999)}"
        
        return f"""
STATEMENT OF WORK (SOW)
=======================

SOW Number: {sow_number}
Client: {client_name}
Project: {project_id}
Effective Date: 2024-01-15
Status: ACTIVE

1. ACTIVE SOW DETAILS
---------------------
Total Contract Value: ${contract_value:,}
Currency: USD
Payment Terms: Net 30

Milestones & Payments:
- Milestone 1 (Kickoff): ${contract_value // 4:,} - PAID
- Milestone 2 (MVP Delivery): ${contract_value // 4:,} - PAID
- Milestone 3 (Beta Release): ${contract_value // 4:,} - PENDING (Due: 2024-06-15)
- Milestone 4 (Go-Live): ${contract_value // 4:,} - SCHEDULED (Due: 2024-08-01)

Contract Dates:
- Start Date: 2024-01-15
- End Date: 2024-12-31
- Duration: 12 months

2. FINANCIAL OVERVIEW
---------------------
Total Billed to Date: ${(contract_value // 4) * 2:,}
Outstanding Amount: ${(contract_value // 4) * 2:,}
Monthly Retainer (Post-Launch): ${monthly_retainer:,}/month

Revenue Recognition:
- Q1 2024: ${contract_value // 4:,}
- Q2 2024: ${contract_value // 4:,}
- Q3 2024: ${contract_value // 4:,} (projected)
- Q4 2024: ${contract_value // 4:,} (projected)

3. INVOICING STATUS
-------------------
INV-2024-001: ${contract_value // 4:,} - PAID (2024-01-20)
INV-2024-002: ${contract_value // 4:,} - PAID (2024-03-15)  
INV-2024-003: ${contract_value // 4:,} - PENDING (Due: 2024-06-15)
INV-2024-004: ${contract_value // 4:,} - DRAFT (Scheduled: 2024-08-01)

4. UPCOMING RENEWALS
--------------------
Current Contract Renewal: 2024-12-01 (60 days notice required)
Proposed Renewal Value: ${int(contract_value * 1.2):,} (+20% increase)
Renewal Status: IN_DISCUSSION

Additional Engagements Under Negotiation:
- Phase 3 Expansion: ${75000:,} - Proposal submitted
- Analytics Add-on: ${25000:,} - Under review
- Managed Services: ${50000:,}/year - Client interested

5. REVENUE CHANNELS
-------------------
- Core Platform Development: 60% of revenue
- Maintenance & Support: 25% of revenue
- Consulting & Advisory: 15% of revenue

6. DELIVERABLES
---------------
- Full-stack web application (React + Python/FastAPI)
- LangGraph AI integration layer
- MongoDB database architecture
- AWS cloud infrastructure (EC2, S3, CloudFront, Lambda)
- CI/CD pipeline (GitHub Actions)
- Comprehensive documentation & training
"""

    @staticmethod
    def generate_tech_spec(project_id: str) -> str:
        """
        Technical document - stack, credentials, implementation log, experiments
        """
        return f"""
TECHNICAL SPECIFICATION DOCUMENT
================================
Project: {project_id}
Version: 2.3
Last Updated: {datetime.now().strftime('%Y-%m-%d')}

1. TECH STACK MATRIX
--------------------
ACTIVE Technologies:
- Frontend: React 18, Next.js 14, TypeScript, TailwindCSS, Redux Toolkit
- Backend: Python 3.12, FastAPI, Pydantic, Motor (async MongoDB)
- AI/ML: LangChain, LangGraph, Groq, ChromaDB, Sentence Transformers
- Database: MongoDB Atlas, Redis (caching)
- Infrastructure: AWS EC2, S3, CloudFront, Lambda, SQS
- DevOps: Docker, Kubernetes, GitHub Actions, Terraform
- Monitoring: Datadog, Sentry, CloudWatch

PLANNED Technologies (Q3-Q4):
- GraphQL API layer
- Apache Kafka for event streaming
- ElasticSearch for advanced search
- Mobile: React Native

DEPRECATED Technologies:
- Angular (migrated to React in Q1 2024)
- PostgreSQL (migrated to MongoDB in 2023)
- Heroku (migrated to AWS)

2. ACCESS AND CREDENTIALS
-------------------------
Production Environment:
- AWS Console: aws.amazon.com/console (SSO via Okta)
- MongoDB Atlas: cloud.mongodb.com (Team login required)
- GitHub Repo: github.com/client/project-nexus (2FA enabled)
- Staging URL: https://staging.clientapp.com
- Production URL: https://app.clientapp.com

API Keys (Stored in AWS Secrets Manager):
- Groq API: groq-prod-xxxxx (rotated monthly)
- Stripe: sk_live_xxxxx (PCI compliant)
- SendGrid: SG.xxxxx (email service)

3. IMPLEMENTATION LOG (Completed)
---------------------------------
- 2024-01-20: Initial project setup and CI/CD configuration - Bob Martinez
- 2024-02-15: User authentication module deployed - Carol Davis
- 2024-03-01: MongoDB schema designed and indexed - David Lee
- 2024-03-15: LangGraph agent swarm MVP complete - Bob Martinez
- 2024-04-01: React dashboard v1.0 released - Carol Davis
- 2024-04-20: Performance optimization (50% faster API responses) - Bob Martinez
- 2024-05-01: Security patches and penetration testing - Emily Wong
- 2024-05-15: ChromaDB vector store integrated - David Lee

4. EXPERIMENT RESULTS
---------------------
A/B Test: Checkout Flow Optimization
- Variant A (Original): 3.2% conversion rate
- Variant B (Simplified): 4.8% conversion rate
- Winner: Variant B (+50% improvement)
- Deployed to Production: 2024-04-10

A/B Test: Landing Page CTA
- Variant A ("Get Started"): 12% click rate
- Variant B ("Try Free"): 18% click rate  
- Winner: Variant B (+50% improvement)
- Deployed to Production: 2024-03-25

A/B Test: Product Page Layout
- Variant A (List View): 2.1 avg time on page
- Variant B (Grid View): 3.4 avg time on page
- Winner: Variant B (+62% engagement)
- Deployed to Production: 2024-05-01

5. ARCHITECTURE DECISIONS
-------------------------
- Microservices pattern with hexagonal architecture
- Event-driven communication using AWS SQS
- JWT-based authentication with refresh tokens
- Rate limiting: 100 requests/minute per user
- Database: Document-oriented for flexibility
"""

    @staticmethod
    def generate_strategy_doc(client_name: str, project_id: str) -> str:
        """
        Strategy document - goals, upsells, competitors, ecosystem
        """
        return f"""
STRATEGIC PLANNING DOCUMENT
===========================
Client: {client_name}
Project: {project_id}
Quarter: Q2 2024

1. STAKEHOLDER INFLUENCE MAP
----------------------------
| Name           | Role                    | Influence | Sentiment  | Notes                           |
|----------------|-------------------------|-----------|------------|----------------------------------|
| Mike Williams  | CTO                     | Very High | Neutral    | Budget controller, ROI focused  |
| John Smith     | VP Engineering          | High      | Champion   | Main sponsor, strong advocate   |
| Sarah Johnson  | Product Owner           | Medium    | Supporter  | Day-to-day contact              |
| Lisa Brown     | Security Lead           | Medium    | Skeptic    | Cloud security concerns         |
| Tom Anderson   | CFO                     | High      | Not Known  | Haven't engaged directly yet    |

2. CLIENT GOALS AND ROADMAP
---------------------------
Q2 2024 Goals:
- Increase user engagement by 25% through improved UX
- Reduce customer churn rate to below 5%
- Achieve 99.9% uptime SLA compliance
- Complete security certification (SOC 2 Type II)

Q3-Q4 2024 Goals:
- Launch mobile application (iOS and Android)
- Expand to 3 new geographic markets (UK, Germany, Japan)
- Achieve 40% YoY revenue growth target
- NPS score improvement to 50+

3. UPSELL OPPORTUNITIES
-----------------------
HIGH POTENTIAL:
- Enterprise Analytics Dashboard: $50,000 - John expressed strong interest
- Managed Services Contract: $75,000/year - Mike requesting proposal
- Custom AI Integration: $35,000 - Sarah mentioned in last meeting

MEDIUM POTENTIAL:
- Training Workshops (5 days): $15,000 - Team needs onboarding
- Extended Support SLA: $2,000/month - Currently on basic plan
- Data Migration Services: $20,000 - Legacy system integration

4. COMPETITIVE LANDSCAPE
------------------------
Direct Competitors:
- Competitor Alpha: Enterprise focus, 40% market share, weak in AI
- Competitor Beta: SMB focus, aggressive pricing, limited features
- Competitor Gamma: New entrant, strong VC funding, marketing heavy

Our Differentiation:
- AI-first architecture with LangGraph
- Superior developer experience
- Faster time-to-value (30% faster implementation)
- Better customer support (4hr response SLA)

5. CLIENT PLATFORM ECOSYSTEM
----------------------------
Current Integrations:
- Salesforce CRM (customer data sync)
- Stripe (payment processing)
- Slack (team notifications)
- Jira (project tracking)
- Google Analytics (usage metrics)

Planned Integrations:
- Hubspot (marketing automation)
- Zendesk (customer support)
- Snowflake (data warehouse)
"""

    @staticmethod
    def generate_marketing_doc(client_name: str, project_id: str) -> str:
        """
        Marketing document - brand guidelines, success stories, testimonials
        """
        return f"""
MARKETING ASSETS & REFERENCES
=============================
Client: {client_name}
Project: {project_id}
Last Updated: {datetime.now().strftime('%Y-%m-%d')}

1. BRAND GUIDELINES
-------------------
Primary Colors:
- Midnight Blue: #1E3A5F (headers, CTAs)
- Electric Teal: #00D4AA (accents, highlights)
- Slate Gray: #6B7280 (body text)
- Pure White: #FFFFFF (backgrounds)

Secondary Colors:
- Success Green: #10B981
- Warning Amber: #F59E0B  
- Error Red: #EF4444

Typography:
- Headings: Inter Bold (700)
- Subheadings: Inter Semibold (600)
- Body Text: Inter Regular (400)
- Code/Technical: JetBrains Mono

Logo Assets:
- Primary Logo: brand.{client_name.lower().replace(' ', '')}.com/logo-primary.svg
- Icon Only: brand.{client_name.lower().replace(' ', '')}.com/icon.svg
- White Version: brand.{client_name.lower().replace(' ', '')}.com/logo-white.svg

Tone of Voice: Professional yet approachable, technically accurate but accessible

2. SUCCESS STORIES
------------------
Case Study 1: "50% Faster Dashboard Load Times"
{client_name} achieved 50% improvement in dashboard performance after
implementing our Redis caching layer and CDN optimization. User engagement
increased by 35% as a result.

Case Study 2: "AI-Powered Customer Insights"
By integrating LangGraph agents, {client_name} automated 80% of their
customer support inquiries, saving 200+ hours per month in manual work.

3. TESTIMONIALS
---------------
John Smith, VP Engineering:
"The team delivered beyond our expectations. The AI integration has
transformed how we handle customer data. Highly recommend!"

Sarah Johnson, Product Owner:
"Working with this team felt like having an extension of our own.
Responsive, knowledgeable, and truly invested in our success."

4. PUBLIC REFERENCES
--------------------
- Website Feature: {client_name} logo displayed on ourcompany.com/customers
- Blog Post: "How {client_name} Scaled with AI" - published 2024-04-15
- Webinar: Joint presentation at TechConf 2024
- Press Release: Partnership announcement on PRNewswire

5. DOCUMENT REFERENCES
----------------------
- Master Services Agreement: contracts/msa-{client_name.lower().replace(' ', '-')}-2024.pdf
- NDA: legal/nda-{client_name.lower().replace(' ', '-')}.pdf
- Security Questionnaire: security/sq-{client_name.lower().replace(' ', '-')}.xlsx
- Onboarding Guide: docs/onboarding-{project_id}.pdf

6. ADDITIONAL EMAIL CONTACTS
----------------------------
General Inquiries: info@{client_name.lower().replace(' ', '')}.com
Technical Support: tech@{client_name.lower().replace(' ', '')}.com
Billing Questions: billing@{client_name.lower().replace(' ', '')}.com
Legal/Contracts: legal@{client_name.lower().replace(' ', '')}.com

7. SUBSCRIPTION & KEY GOALS
---------------------------
Current Plan: Enterprise (Annual)
Key Success Metrics:
- Monthly Active Users: 10,000+
- API Calls/Day: 500,000
- Data Storage: 500GB
- SLA Target: 99.9% uptime
"""

    @staticmethod
    def get_all_test_payloads(client_id: str, project_id: str) -> List[Dict[str, str]]:
        """Returns all test documents for comprehensive agent testing."""
        client_name = client_id.replace("_", " ").title()
        return [
            {"filename": "account_overview.txt", "text": MockDataGenerator.generate_account_overview(client_name, project_id)},
            {"filename": "meeting_notes.txt", "text": MockDataGenerator.generate_meeting_notes(client_name, project_id)},
            {"filename": "sow_contract.txt", "text": MockDataGenerator.generate_sow_content(client_name, project_id)},
            {"filename": "tech_specification.txt", "text": MockDataGenerator.generate_tech_spec(project_id)},
            {"filename": "strategy_plan.txt", "text": MockDataGenerator.generate_strategy_doc(client_name, project_id)},
            {"filename": "marketing_assets.txt", "text": MockDataGenerator.generate_marketing_doc(client_name, project_id)}
        ]
