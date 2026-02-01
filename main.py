import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from agno.agent import Agent
from agno.models.groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = Groq(api_key=GROQ_API_KEY, id="llama-3.1-8b-instant")

st.set_page_config(page_title="Elite Financial Intelligence Coach", layout="wide")
st.title("Elite Financial Intelligence Coach 💬")

voices = {
    "Conservative Advisor": "You are a highly disciplined, risk-averse Wealth Protector. Your focus is on capital preservation, debt elimination, and long-term security. You view unnecessary spending as a threat to the user's future. Your tone is professional, stern, and focused on mathematical certainty.",
    "Fun Saver": "You are a high-energy, motivational Financial Buddy. Your philosophy is 'Save Hard, Play Hard.' You help users find 'hidden money' in their spending so they can fund their dreams without feeling deprived. You use emojis, humor, and enthusiastic encouragement to make budgeting feel like a win.",
    "Analytical Guru": "You are a meticulous Data Scientist and Quantitative Strategist. You care about trends, standard deviations, and spending velocities. You provide deep-dive insights into categorical anomalies and use data-driven forecasting to map out the user's financial trajectory with surgical precision."
}

selected_voice = st.selectbox("Choose Advisor Persona", list(voices.keys()))

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "uploaded_file": None,
        "goal_amount": None,
        "goal_months": None,
        "monthly_salary": None,
        "file_uploaded_message_added": False,
        "report_generated": False
    }

if "last_voice" not in st.session_state:
    st.session_state.last_voice = selected_voice

if st.session_state.last_voice != selected_voice:
    st.session_state.chat_history = []
    st.session_state.user_data = {
        "uploaded_file": None,
        "goal_amount": None,
        "goal_months": None,
        "monthly_salary": None,
        "file_uploaded_message_added": False,
        "report_generated": False
    }
    st.session_state.last_voice = selected_voice

if not st.session_state.chat_history:
    agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} Greet the user with a very detailed and persona-rich introduction. Explain exactly how you are going to transform their finances once they upload their transaction file. Be extremely verbose.")
    resp = agent.run("Introduce yourself and request the transaction file.")
    st.session_state.chat_history.append({"sender": "coach", "message": resp.content})

if st.session_state.user_data["uploaded_file"] is None:
    uploaded_file = st.file_uploader("Upload Transaction Ledger (CSV/XLSX):", type=["csv","xlsx"])
    if uploaded_file is not None:
        st.session_state.user_data["uploaded_file"] = uploaded_file
        agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} The user has provided their data. Celebrate this first step toward financial mastery with a verbose response and ask them for their primary financial goal amount.")
        resp = agent.run("Acknowledge file upload and ask for the target savings goal.")
        st.session_state.chat_history.append({"sender": "coach", "message": resp.content})
        st.rerun()

user_input = st.chat_input("Type your response or question here...")

if user_input:
    st.session_state.chat_history.append({"sender": "user", "message": user_input})
    user_data = st.session_state.user_data
    input_val = user_input.replace(',', '').replace('$', '').strip()
    
    agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} Engage in a verbose, detailed conversation. If the user provides a number, validate it through the lens of your persona and move to the next logical question (Goal -> Timeframe -> Monthly Income).")

    if user_data["goal_amount"] is None:
        if input_val.replace('.', '', 1).isdigit():
            user_data["goal_amount"] = float(input_val)
            resp = agent.run(f"User set goal to ${input_val}. Now, in a very verbose manner, ask for the timeframe in months to achieve this.")
            response = resp.content
        else: response = "I require a numeric value to begin the projection. What is our target amount?"
    elif user_data["goal_months"] is None:
        if input_val.isdigit():
            user_data["goal_months"] = int(input_val)
            resp = agent.run(f"User has {input_val} months. Now, with deep persona flair, ask for their total monthly net income.")
            response = resp.content
        else: response = "Please specify the duration in months so I can calculate the necessary savings velocity."
    elif user_data["monthly_salary"] is None:
        if input_val.replace('.', '', 1).isdigit():
            user_data["monthly_salary"] = float(input_val)
            response = "Mathematical parameters locked. I am now synthesizing your exhaustive financial intelligence report. One moment..."
        else: response = "I need your monthly income figure to finalize the baseline for our models."
    else:
        user_data["report_generated"] = False
        response = "Context updated. Recalculating all financial models and updating your strategic roadmap..."

    st.session_state.chat_history.append({"sender": "coach", "message": response})
    st.rerun()

for entry in st.session_state.chat_history:
    with st.chat_message("user" if entry["sender"] == "user" else "assistant"):
        st.markdown(entry["message"])

user_data = st.session_state.user_data
if all([user_data["uploaded_file"], user_data["goal_amount"], user_data["goal_months"], user_data["monthly_salary"]]) and not user_data["report_generated"]:
    if user_data["uploaded_file"].name.endswith(".csv"): df = pd.read_csv(user_data["uploaded_file"])
    else: df = pd.read_excel(user_data["uploaded_file"])

    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    amt_col = next((c for c in df.columns if "amount" in c.lower()), None)
    cat_col = next((c for c in df.columns if "category" in c.lower() or "merchant" in c.lower()), None)

    if date_col: df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    if amt_col: df[amt_col] = pd.to_numeric(df[amt_col], errors='coerce')
    df = df.dropna(subset=[amt_col, cat_col])

    recent_days = 60
    cutoff = datetime.now() - timedelta(days=recent_days)
    df_recent = df[df[date_col] >= cutoff] if date_col else df
    
    monthly_spending = df_recent.groupby(df_recent[date_col].dt.to_period('M'))[amt_col].sum().mean() if date_col else df_recent[amt_col].sum() / 2
    monthly_savings = max(user_data["monthly_salary"] - monthly_spending, 0)
    savings_rate = (monthly_savings / user_data["monthly_salary"] * 100)
    
    top_cats = df_recent.groupby(cat_col)[amt_col].sum().sort_values(ascending=False).head(15).to_dict()
    recurring = df_recent.groupby([cat_col, amt_col]).size().reset_index(name='count')
    recurring_dict = recurring[recurring['count'] > 1].to_dict()

    financial_agent = Agent(
        name="Advanced Financial Intelligence Agent",
        model=llm,
        instructions=f"""
You are the {selected_voice} Financial Advisor. 
{voices[selected_voice]}

STRICT FINANCIAL ANCHORS:
- PRIMARY SAVINGS GOAL: ${user_data['goal_amount']:.2f}
- STRATEGIC TIMEFRAME: {user_data['goal_months']} months
- MONTHLY NET INCOME: ${user_data['monthly_salary']:.2f}

RAW DATASET SUMMARY:
- Calculated Avg Monthly Spend: ${monthly_spending:.2f}
- Current Monthly Savings: ${monthly_savings:.2f}
- Savings Rate: {savings_rate:.1f}%
- Top Expenditure Categories: {top_cats}
- Detected Recurring Patterns: {recurring_dict}

CORE MISSION (BE EXTREMELY VERBOSE, DETAILED, AND ANALYTICAL):
1. EXECUTIVE FINANCIAL HEALTH AUDIT:
   - Provide a 'Health Grade' (A+ to F).
   - Evaluate the objective feasibility of reaching ${user_data['goal_amount']:.2f} in {user_data['goal_months']} months based on current velocity.
   - Use bold headers and professional summaries.

2. QUANTITATIVE PROJECTION & FORECASTING:
   - Create a detailed month-by-month projection table for the next {user_data['goal_months']} months.
   - Highlight the 'Savings Gap'—the exact amount needed to increase monthly savings to hit the goal early.

3. SPENDING LEAKAGE & ANOMALY DETECTION:
   - Perform a deep-dive into the top 5 categories. Flag anything exceeding 15% of income.
   - Contrast spending against the 50/30/20 rule of thumb.
   - Detect 'Gray Charges'—subscriptions or repeating fees that are draining capital.

4. RISK ASSESSMENT & STRESS TEST:
   - Simulate an 'Emergency Scenario' (e.g., a 15% income drop or a $1,500 surprise expense). 
   - Show how this event shifts the goal timeline.

5. THREE-TIER STRATEGIC ROADMAP:
   - Tier 1: Aggressive (High discipline, rapid goal achievement).
   - Tier 2: Balanced (Current pace with minor optimizations).
   - Tier 3: Defensive (Safety-first approach with emergency fund prioritization).

6. PERSONA-DRIVEN CLOSING & INTERACTION:
   - Ask a highly sophisticated, verbose question based on your persona to provoke deeper user thought.
   - Respond directly to the user's last message: {st.session_state.chat_history[-2]['message'] if len(st.session_state.chat_history) > 1 else 'None'}.

OUTPUT FORMATTING: 
- Use Markdown only. 
- Use complex tables, bold callouts, and blockquotes for emphasis. 
- Ensure the tone remains 100% consistent with the {selected_voice} persona.
"""
    )
    report = financial_agent.run(st.session_state.chat_history[-2]["message"] if len(st.session_state.chat_history) > 1 else "Initial Full Intelligence Report Request")
    st.session_state.chat_history.append({"sender": "coach", "message": report.content if hasattr(report, "content") else report})
    user_data["report_generated"] = True
    st.rerun()