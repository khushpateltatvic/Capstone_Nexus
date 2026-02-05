from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.logging_config import logger

# Comprehensive Section Definitions for high accuracy
SECTION_DEFINITIONS = """
You are a highly analytical classification agent for an Account Intelligence Platform.

Your task is to classify incoming text, emails, notes, or tickets into EXACTLY ONE of the following 7 Sections based on the semantic meaning.

### SECTION 1: UNIVERSAL CONTEXT (Client Health, High-Level Engagement)
- **Use for:** High-level account summaries, industry news affecting the client, leadership changes, overall engagement health updates, "Big Picture" context.
- **Examples:** "Client just acquired a competitor.", "Engagement health is declining due to budget cuts.", "Quarterly Business Review summary."

### SECTION 2: OPERATIONS & STATUS (Day-to-Day Execution)
### SECTION 2: OPERATIONS & STATUS (Day-to-Day Execution)
- **Use for:** Tactical updates, project status, blockers, specific task updates, meeting notes about delivery, escalation requests, "server down" alerts, bug reports management.
- **Examples:** "The API integration is blocked by firewall issues.", "Meeting notes: Action items assigned to Dev Team.", "Escalating ticket #123 due to SLA breach.", "Deployment successful.", "Prod is down", "System crash"

### SECTION 3: TECHNICAL INTELLIGENCE (Architecture, Stack, Access)
- **Use for:** Specific technology choices, architectural decisions, code implementation details, credential sharing (references), experiment results, tech stack changes.
- **Examples:** "We are migrating to Next.js.", "Database schema for user profiles updated.", "AWS credentials stored in vault.", "A/B test results for new UI."

### SECTION 4: COMMERCIAL & LEGAL (Money, Contracts, SOWs)
- **Use for:** Budgets, invoices, SOW (Statement of Work) details, contract renewals, financial discussions, billing disputes.
- **Examples:** "SOW for Q3 signed.", "Client requesting discount on next invoice.", "Renewal conversation scheduled for next week.", "Budget approval pending."

### SECTION 5: STRATEGY (Influence, Goals, Politics)
- **Use for:** Stakeholder mapping (who influences whom), long-term client goals, political landscape, expansion opportunities, competitor intel.
- **Examples:** "John is the key decision maker now.", "Client wants to expand into APAC market next year.", "Competitor X is pitching to our client.", "Champion stakeholder left the company."

### SECTION 6: MARKETING (Brand, Success Stories)
- **Use for:** Brand guidelines, logo usage, testimonial approvals, case study drafts, public references.
- **Examples:** "Here are the new brand color codes.", "Client agreed to a video testimonial.", "Case study draft approved for publication."

### SECTION 7: MISC / UNSORTED (Feedback, Random)
- **Use for:** Low-context notes, raw feedback without clear category, personal notes, scheduling logistics not related to project delivery.
- **Examples:** "Great session today.", "Lunch meeting proposed.", "Attached is the file you asked for (no context).", "Feedback: UI looks clean."

---
**INSTRUCTIONS:**
1. Analyze the input text carefully.
2. Determine the *primary intent*.
3. Return ONLY the integer digit of the section (1-7).
4. If ambiguous, choose the most specific operational or strategic fit. If completely unknown, use 7.
"""

def get_classifier_chain():
    llm = ChatGroq(temperature=0, model_name=settings.GROQ_MODEL_NAME, api_key=settings.GROQ_API_KEY)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{definitions}"),
        ("human", "Classify this text:\n{text}")
    ])
    
    chain = prompt | llm | (lambda x: x.content.strip())
    return chain

async def classify_text(text: str) -> int:
    chain = get_classifier_chain()
    result = await chain.ainvoke({"definitions": SECTION_DEFINITIONS, "text": text})
    logger.debug(f"Classifier LLM raw output: {result}")
    
    # Simple parsing logic to handle potential chatty responses (though temp=0 helps)
    try:
        # Extract first digit found
        import re
        match = re.search(r'\d', result)
        if match:
            return int(match.group())
        return 7
    except Exception:
        return 7
