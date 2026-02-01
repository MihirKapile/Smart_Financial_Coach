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
            "Detect 'Gray Charges': recurring subscriptions the user might have forgotten.",
            "Detect Anomalies: Spending that is 50% higher than the category average.",
            "Return a Markdown list of specific transactions to review."
        ]
    )