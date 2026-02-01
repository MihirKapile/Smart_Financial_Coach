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

voices = {
    "Conservative Advisor": "Focus on savings, avoid unnecessary spending, highlight risks.",
    "Fun Saver": "Encourage small treats, fun spending, but note where to save.",
    "Analytical Guru": "Give data-driven breakdowns, highlight patterns, anomalies, and trends."
}
selected_voice = st.selectbox("Choose Advisor Voice", list(voices.keys()))

if uploaded_file:
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

    # If any column not detected, pass all columns and let LLM handle it
    if not all([date_col, amount_col, category_col]):
        st.warning("Could not auto-detect all key columns. Passing full data to LLM for analysis.")
        df_to_send = df
    else:
        # --- Ensure correct types ---
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
        df = df.dropna(subset=[amount_col, category_col])

        # --- Filter recent 30–60 days ---
        recent_days = st.slider("Select recent days of data to analyze", min_value=30, max_value=60, value=30)
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        df_to_send = df[df[date_col] >= cutoff_date]

    # --- LLM Agent: Full Financial Advisor ---
    financial_agent = Agent(
        name="Full Financial Advisor",
        model=llm,
        instructions=f"""
You are a {selected_voice} financial advisor.
You receive transaction data in any CSV/Excel structure.
Step 1: Detect key columns (date, amount, category), even if names are unconventional.
Step 2: Clean the data (handle empty rows/columns, invalid amounts, messy data).
Step 3: Analyze spending:
    - Monthly average spending
    - Top 3 spending categories
    - Most expensive months
Step 4: Forecast goal progress:
    - Average savings
    - Total savings
    - Are they on track to meet the goal of ${goal_amount} in {goal_months} months?
Step 5: Detect recurring subscriptions and gray charges (forgotten free trials, mystery charges).
Step 6: Generate actionable advice in a fun, friendly, readable tone.
Step 7: Present a cohesive report in Markdown with headings, bullet points, and numbers.
Respond in Markdown format.
"""
    )

    # --- Run agent ---
    report = financial_agent.run({
        "transactions": df_to_send.to_dict(orient="records"),
        "goal_amount": goal_amount,
        "goal_months": goal_months
    })

    # --- Display final report ---
    st.subheader("AI Advisor Insights")
    st.markdown(report.content)