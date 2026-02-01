from agno.agent import Agent
from agno.models.groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_auditor_agent():
    return Agent(
        name="Auditor",
        model=Groq(id="llama-3.3-70b-versatile"),
        instructions=[
            "You are a forensic financial auditor.",
            "1. List EVERY recurring transaction (same amount, same vendor, different dates).",
            "2. Identify any transaction over $100 as a potential anomaly.",
            "3. ONLY report on transactions found in the Knowledge Base. If no data is found, say 'No data retrieved'.",
            "4. Provide a raw breakdown of spending by category (Food, Bills, etc.)."
        ]
    )