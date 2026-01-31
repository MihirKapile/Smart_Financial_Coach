from agno.agent import Agent
from agno.team import Team
from agno.models.groq import Groq
from agents.auditor import get_auditor_agent
from agents.forecaster import get_forecaster_agent
from tools.knowledge import get_knowledge_base
from tools.visualizer import generate_spending_chart

def get_smart_coach(knowledge_base,persona_name="Wealth Architect"):
    """
    Orchestrates the specialist agents and applies the behavioral persona.
    """
    
    persona_prompts = {
        "Tough Love": (
            "You are a brutally honest, sarcastic financial coach. "
            "Mock the user's wasteful spending and 'gray charges' with humor. "
            "Be aggressive about hitting the savings goal."
        ),
        "Wealth Architect": (
            "You are a professional, data-driven wealth strategist. "
            "Focus on ROI, compound interest, and logical optimization. "
            "Use formal and precise language."
        ),
        "Bestie": (
            "You are a supportive, encouraging financial best friend. "
            "Use plenty of emojis 💸✨. Focus on small wins and positive reinforcement."
        )
    }

    auditor_agent = get_auditor_agent()
    forecaster_agent = get_forecaster_agent()

    return Team(
        name="Lead Coach Orchestrator",
        model=Groq(id="llama-3.1-8b-instant"),
        knowledge=knowledge_base,
        search_knowledge=True,
        read_chat_history=False,
        members=[auditor_agent, forecaster_agent],
        tools=[generate_spending_chart],
        delegate_to_all_members=True,
        instructions=[
    f"Persona: {persona_name}, {persona_prompts.get(persona_name, 'Wealth Architect')}",
    "1. INITIAL DATA MINING: Search the Knowledge Base for the user's last 3-6 months of transactions.",
    
    "2. SPENDING CATEGORIZATION & VISUALIZATION:",
    "   - Summarize total spending by category (e.g., Housing, Food, Entertainment, Subscriptions).",
    "   - MANDATORY: Call 'generate_spending_chart' with a list of category-amount pairs to visualize the macro-budget.",
    
    "3. SUBSCRIPTION & GRAY CHARGE AUDIT:",
    "   - Identify recurring payments (Netflix, Gym, etc.) and 'Gray Charges' (unused trials or hidden fees).",
    "   - Provide a Markdown table of these costs and calculate their annual impact.",
    
    "4. GOAL FEASIBILITY & MATHEMATICAL FORECASTING:",
    "   - Perform a Gap Analysis: Calculate Required Monthly Savings vs. Current Monthly Surplus.",
    "   - Provide a 'Yes/No' verdict on saving ${goal_amount} in {months} months.",
    "   - MANDATORY: Call 'generate_spending_chart' using a 'bar' type to compare 'Current Savings' vs 'Target Savings' trajectory.",
    
    "5. BEHAVIORAL DEEP DIVE:",
    "   - Identify one spending anomaly (e.g., 'You spend 30% more on Friday nights').",
    "   - Call out this behavioral pattern in your persona's voice.",
    
    "6. FINAL ACTION PLAN:",
    "   - Give exactly 3 specific, actionable 'Cuts' to bridge the savings gap.",
    "   - End with a single 'Power Move' the user can do in the next 10 minutes to save money."
],
        markdown=True
    )