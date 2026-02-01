from agno.agent import Agent
from agno.team import Team
from agno.models.groq import Groq
from agno.models.google import Gemini
from agents.auditor import get_auditor_agent
from agents.forecaster import get_forecaster_agent
from tools.knowledge import get_knowledge_base
from tools.visualizer import generate_spending_chart
from agents.visual_analyst import get_visual_analyst_agent
from dotenv import load_dotenv
load_dotenv()
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
    visual_analyst_agent = get_visual_analyst_agent()

    return Team(
        name="Lead Coach Orchestrator",
        model=Groq(id="llama-3.3-70b-versatile"),
        knowledge=knowledge_base,
        search_knowledge=True,
        read_chat_history=False,
        delegate_to_all_members=True,
        members=[auditor_agent, forecaster_agent,visual_analyst_agent],
        tools=[generate_spending_chart],
        instructions=[
            f"Adhere strictly to this Persona: {persona_name}, {persona_prompts.get(persona_name)}",
            "STEP 1: Auditor extracts 3-6 months of transactions from Knowledge Base.",
            "STEP 2: Visual Analyst generates the Essential vs Non-Essential PIE CHART.",
            "STEP 3: Forecaster calculates the gap for the user's specific goal.",
            "STEP 4: Visual Analyst generates the Savings Trajectory BAR CHART.",
            "STEP 5: Synthesize a final deep analysis in your assigned Persona voice."
        ],
        markdown=True,
    )