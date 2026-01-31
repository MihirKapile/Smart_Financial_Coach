from agno.agent import Agent
from agno.models.groq import Groq

def get_forecaster_agent():
    return Agent(
        name="Forecaster",
        model=Groq(id="llama-3.1-8b-instant"),
        instructions=[
            "Calculate the path to the user's financial goal.",
            "If they are off-track, suggest 3 'Guilt-Free' swaps (e.g., Brew coffee vs. Buying).",
            "Be encouraging and use data to prove your points."
        ]
    )