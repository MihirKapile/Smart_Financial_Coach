from tools.visualizer import generate_spending_chart
from agno.agent import Agent
from agno.models.groq import Groq
from dotenv import load_dotenv
load_dotenv()

def get_visual_analyst_agent():
    return Agent(
        name="visual_analyst",
        role="Data Visualization Specialist",
        model=Groq(id="llama-3.3-70b-versatile"),
        instructions=[
            "You are the ONLY member authorized to call 'generate_spending_chart'.",
            "When the Auditor provides data, you must transform it into exactly TWO charts:",
            "1. A PIE chart showing 'Essential' vs 'Non-Essential' totals.",
            "2. A BAR chart showing 'Current Monthly Savings' vs 'Required Monthly Savings' ($600/mo).",
            "Format the tool input exactly as a list of dictionaries: [{'label': 'Essential', 'value': 2100}, {'label': 'Non-Essential', 'value': 800}]",
            "CRITICAL: Do not describe the chart in text. Just call the tool."
        ]
    )