import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from agno.agent import Agent
from agno.models.groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Initialize LLM ---
llm = Groq(api_key=GROQ_API_KEY, id="llama-3.1-8b-instant")

st.set_page_config(page_title="Smart Financial Coach", layout="wide")
st.title("Smart Financial Coach 💰")

# --- File uploader ---
uploaded_file = st.file_uploader(
    "Upload your transactions CSV/Excel (any structure)",
    type=["csv", "xlsx"]
)

# --- User inputs ---
goal_amount = st.number_input("Set your financial goal amount ($)", value=3000.0)
goal_months = st.number_input("Timeframe to reach goal (months)", value=6, min_value=1)
monthly_salary = st.number_input("Enter your monthly salary ($)", value=3000.0)

# --- Persona definitions ---
voices = {
    "Conservative Advisor": """
Focus on safety and long-term planning. Highlight risks and ways to save rigorously.
Give advice in a formal, cautious tone. Emphasize security over fun spending.
Use professional and serious language.
""",
    "Fun Saver": """
Encourage fun, small treats, and enjoyment while saving. Be playful and cheerful.
Give actionable advice in a friendly, motivational, and lighthearted tone.
Use jokes, fun analogies, or playful comments when appropriate.
""",
    "Analytical Guru": """
Give data-driven insights and patterns. Focus on numbers, trends, and anomalies.
Use charts, percentages, and comparisons in your explanations.
Be precise, analytical, and professional in tone.
"""
}

selected_voice = st.selectbox("Choose Advisor Voice", list(voices.keys()))

# --- Trigger button ---
if uploaded_file and st.button("Generate Insights"):

    # --- Read file ---
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # --- Auto-detect key columns ---
    column_names = df.columns
    date_col = next((c for c in column_names if "date" in c.lower()), None)
    amount_col = next((c for c in column_names if "amount" in c.lower()), None)
    category_col = next((c for c in column_names if "category" in c.lower() or "merchant" in c.lower()), None)

    # --- Data cleaning ---
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    if amount_col:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
    df = df.dropna(subset=[amount_col, category_col])

    # --- Filter recent days ---
    recent_days = st.slider("Select recent days of data to analyze", min_value=30, max_value=60, value=30)
    if date_col:
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        df_to_send = df[df[date_col] >= cutoff_date]
    else:
        df_to_send = df

    # --- Spending per category graph ---
    st.subheader("Spending per Category")
    category_summary = df_to_send.groupby(category_col)[amount_col].sum().sort_values(ascending=False)
    st.bar_chart(category_summary)

    # --- Spending over time graph ---
    if date_col:
        st.subheader("Spending Over Time")
        df_time = df_to_send.groupby(date_col)[amount_col].sum().sort_index()
        st.line_chart(df_time)

    # --- LLM Agent: Full Financial Advisor with persona ---
    financial_agent = Agent(
        name="Full Financial Advisor",
        model=llm,
        instructions=f"""
    You are a {selected_voice} financial advisor.
    {voices[selected_voice]}

    You have received the following transaction data (recent {recent_days} days):
    {df_to_send.to_dict(orient='records')}

    Financial Goal: Save ${goal_amount} in {goal_months} months
    Monthly Salary: ${monthly_salary}

    Your task:
    - Analyze the data and provide insights (spending, top categories, most expensive months, recurring subscriptions, grey charges, goal progress, savings tips)
    - Generate actionable advice **in the selected persona voice**
    - Do NOT include internal step numbers (Step 1, Step 2, etc.) in the final report
    - Present a **cohesive, flowing Markdown report** that reads like a friendly report
    - Include headings, bullet points, and numbers where appropriate, but keep it smooth
    - Make the tone match the persona:
        - Fun Saver → playful, cheerful, motivating
        - Conservative Advisor → formal, cautious, risk-aware
        - Analytical Guru → precise, data-driven, analytical
    - Respond strictly in Markdown

    Example of flow:
    - Start with a friendly introduction
    - Summarize key data insights naturally
    - Give actionable tips/advice in persona style
    - End with encouragement/recommendation
    """
    )


    # --- Run agent ---
    report = financial_agent.run({})

    # --- Display final report ---
    st.subheader("AI Advisor Insights")
    if hasattr(report, "content"):
        st.markdown(report.content)
    else:
        st.markdown(report)
