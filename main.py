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
    description_col = next((c for c in column_names if "description" in c.lower()), None)

    # --- Data cleaning ---
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    if amount_col:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
    df = df.dropna(subset=[amount_col, category_col])

    # --- Filter last 60 days ---
    recent_days = 60
    if date_col:
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        df_recent = df[df[date_col] >= cutoff_date]
    else:
        df_recent = df

    # --- Monthly Spending Calculation ---
    if date_col:
        df_recent['month'] = df_recent[date_col].dt.to_period('M')
        monthly_spending = df_recent.groupby('month')[amount_col].sum().mean()
    else:
        monthly_spending = df_recent[amount_col].sum() / (recent_days/30)

    monthly_savings = max(monthly_salary - monthly_spending, 0)
    savings_rate = monthly_savings / monthly_salary * 100
    total_spent = df_recent[amount_col].sum()

    # --- Recurring and "Gray Charges" Detection ---
    recurring = df_recent.groupby([category_col, amount_col]).size().reset_index(name='count')
    recurring = recurring[recurring['count'] > 1]

    # Optional: detect suspicious low-frequency charges that might be forgotten subscriptions
    gray_charges = df_recent[df_recent[amount_col] < monthly_salary*0.05]  # small charges
    gray_charges = gray_charges.groupby([category_col, amount_col]).size().reset_index(name='count')
    gray_charges = gray_charges[gray_charges['count'] > 1]

    # --- Top Categories ---
    top_categories = df_recent.groupby(category_col)[amount_col].sum().sort_values(ascending=False).head(5)

    # --- Persona-aware Spending per Category graph ---
    st.subheader("Spending per Category")
    category_summary = df_recent.groupby(category_col)[amount_col].sum().reset_index()
    max_spent = category_summary[amount_col].max()

    if selected_voice == "Fun Saver":
        category_summary['label'] = category_summary.apply(
            lambda row: f"{row[category_col]} {'💸' if row[amount_col] >= max_spent*0.7 else ''}", axis=1
        )
        chart = alt.Chart(category_summary).mark_bar(color='#FF6F61').encode(
            x=alt.X('label:N', sort='-y', title='Category'),
            y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
            tooltip=[category_col, amount_col]
        )
    elif selected_voice == "Conservative Advisor":
        total_spent_sum = category_summary[amount_col].sum()
        category_summary['color'] = category_summary[amount_col].apply(
            lambda x: 'red' if x/total_spent_sum >= 0.3 else 'steelblue'
        )
        chart = alt.Chart(category_summary).mark_bar().encode(
            x=alt.X(f'{category_col}:N', sort='-y', title='Category'),
            y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
            color=alt.Color('color:N', scale=None),
            tooltip=[category_col, amount_col]
        )
    else:
        category_summary['percent'] = category_summary[amount_col] / category_summary[amount_col].sum() * 100
        chart = alt.Chart(category_summary).mark_bar(color='#4E79A7').encode(
            x=alt.X(f'{category_col}:N', sort='-y', title='Category'),
            y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
            tooltip=[category_col, amount_col, alt.Tooltip('percent:Q', format='.1f', title='% of Total')]
        )

    st.altair_chart(chart, use_container_width=True)

    # --- Persona-aware Spending Over Time ---
    if date_col:
        st.subheader("Spending Over Time")
        df_time = df_recent.groupby(date_col)[amount_col].sum().reset_index()
        chart_time = alt.Chart(df_time).mark_line(point=True).encode(
            x=alt.X(f'{date_col}:T', title='Date'),
            y=alt.Y(f'{amount_col}:Q', title='Total Spent ($)'),
            tooltip=[date_col, amount_col]
        )
        st.altair_chart(chart_time, use_container_width=True)

    # --- LLM Persona Agent: Full Personalized Analysis ---
    financial_agent = Agent(
        name="Full Financial Advisor",
        model=llm,
        instructions=f"""
You are a {selected_voice} financial advisor.
{voices[selected_voice]}

You have the following structured data:
- Total spent in last {recent_days} days: ${total_spent:.2f}
- Average monthly spending: ${monthly_spending:.2f}
- Monthly salary: ${monthly_salary:.2f}
- Monthly savings: ${monthly_savings:.2f} ({savings_rate:.1f}% savings rate)
- Goal amount: ${goal_amount:.2f}
- Goal timeframe: {goal_months} months
- Top categories: {top_categories.to_dict()}
- Recurring subscriptions: {recurring.to_dict()}
- Gray charges / forgotten small recurring expenses: {gray_charges.to_dict()}

Tasks:
1. **Personalized Goal Forecasting**
   - Determine if user is on track to reach goal within {goal_months} months.
   - If not, suggest exact amounts to cut or save to meet goal.
   - Include "what-if" scenarios: e.g., cancel subscriptions, reduce top category spending.

2. **Subscription & Gray Charge Detector**
   - Present all recurring subscriptions, free trials turned paid, and other gray charges in a clear list.
   - Highlight potential savings if canceled.

3. **Category-wise Spending Analysis**
   - Identify overspending categories and trends.
   - Include actionable tips tailored to persona.

4. **Actionable Recommendations**
   - Provide a prioritized list of steps the user can take immediately.
   - Include motivational guidance per persona.

5. **Report Format**
   - Markdown only, use tables, bullet points, percentages.
   - Provide in-depth, persona-consistent commentary.

Generate a detailed report combining all sections above with calculations and realistic forecasts.
"""
    )

    report = financial_agent.run({})

    st.subheader("AI Advisor Insights")
    if hasattr(report, "content"):
        st.markdown(report.content)
    else:
        st.markdown(report)
