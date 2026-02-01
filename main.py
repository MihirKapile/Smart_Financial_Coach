import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from agno.agent import Agent
from agno.models.groq import Groq
import os
from dotenv import load_dotenv
import altair as alt

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
    recent_days = 60
    if date_col:
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        df_to_send = df[df[date_col] >= cutoff_date]
    else:
        df_to_send = df

    # --- Persona-aware Spending per Category graph ---
    st.subheader("Spending per Category")
    category_summary = df_to_send.groupby(category_col)[amount_col].sum().reset_index()
    max_spent = category_summary[amount_col].max()

    if selected_voice == "Fun Saver":
        # Add emoji to top 3 categories
        category_summary['label'] = category_summary.apply(
            lambda row: f"{row[category_col]} {'💸' if row[amount_col] >= max_spent*0.7 else ''}", axis=1
        )
        chart = alt.Chart(category_summary).mark_bar(color='#FF6F61').encode(
            x=alt.X('label:N', sort='-y', title='Category'),
            y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
            tooltip=[category_col, amount_col]
        )
    elif selected_voice == "Conservative Advisor":
        # Highlight categories >30% of total as red
        total_spent = category_summary[amount_col].sum()
        category_summary['color'] = category_summary[amount_col].apply(
            lambda x: 'red' if x/total_spent >= 0.3 else 'steelblue'
        )
        chart = alt.Chart(category_summary).mark_bar().encode(
            x=alt.X(f'{category_col}:N', sort='-y', title='Category'),
            y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
            color=alt.Color('color:N', scale=None),
            tooltip=[category_col, amount_col]
        )
    else:  # Analytical Guru
        category_summary['percent'] = category_summary[amount_col] / category_summary[amount_col].sum() * 100
        chart = alt.Chart(category_summary).mark_bar(color='#4E79A7').encode(
            x=alt.X(f'{category_col}:N', sort='-y', title='Category'),
            y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
            tooltip=[category_col, amount_col, alt.Tooltip('percent:Q', format='.1f', title='% of Total')]
        )

    st.altair_chart(chart, use_container_width=True)

    # --- Persona-aware Spending over Time graph ---
    if date_col:
        st.subheader("Spending Over Time")
        df_time = df_to_send.groupby(date_col)[amount_col].sum().reset_index()

        if selected_voice == "Fun Saver":
            chart_time = alt.Chart(df_time).mark_line(color='#FF6F61', point=True).encode(
                x=alt.X(f'{date_col}:T', title='Date'),
                y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
                tooltip=[date_col, amount_col]
            )
        elif selected_voice == "Conservative Advisor":
            avg_spent = df_time[amount_col].mean()
            chart_time = alt.Chart(df_time).mark_line(color='steelblue').encode(
                x=alt.X(f'{date_col}:T', title='Date'),
                y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
                tooltip=[date_col, amount_col]
            ) + alt.Chart(df_time).mark_rule(color='red', strokeDash=[5,5]).encode(
                y=alt.value(avg_spent),
                tooltip=alt.TooltipValue(f"Average: ${avg_spent:.2f}")
            )
        else:  # Analytical Guru
            chart_time = alt.Chart(df_time).mark_line(color='#4E79A7').encode(
                x=alt.X(f'{date_col}:T', title='Date'),
                y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
                tooltip=[date_col, amount_col]
            )
        st.altair_chart(chart_time, use_container_width=True)

    # --- LLM Agent: Full Financial Advisor with persona and natural flow ---
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
- Analyze the data and provide insights: spending, top categories, most expensive months, recurring subscriptions, grey charges, goal progress, savings tips
- Generate actionable advice in persona voice
- DO NOT include internal step numbers in the final report
- Present a cohesive, flowing Markdown report
- Make tone match the persona:
    - Fun Saver → playful, cheerful, motivating
    - Conservative Advisor → formal, cautious, risk-aware
    - Analytical Guru → precise, data-driven, analytical
- Respond strictly in Markdown
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
