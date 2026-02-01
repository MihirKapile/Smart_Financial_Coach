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
    "Conservative Advisor": "You are a highly disciplined Wealth Protector. Focus on mathematical certainty and risk mitigation. Your tone is professional, stern, and focused on security.",
    "Fun Saver": "You are a high-energy Financial Buddy. Your philosophy is 'Save Hard, Play Hard.' Use emojis, humor, and enthusiastic encouragement. Be extremely verbose and persona-rich.",
    "Analytical Guru": "You are a meticulous Quantitative Strategist. You provide deep-dive insights into categorical anomalies with surgical precision and data-driven logic."
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
        "report_generated": False,
        "viz_data": None
    }

if "last_voice" not in st.session_state:
    st.session_state.last_voice = selected_voice

if st.session_state.last_voice != selected_voice:
    st.session_state.chat_history = []
    st.session_state.user_data = {k: None for k in st.session_state.user_data}
    st.session_state.last_voice = selected_voice

if not st.session_state.chat_history:
    agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} Greet the user with an extremely verbose introduction and request the transaction file.")
    resp = agent.run("Introduce yourself.")
    st.session_state.chat_history.append({"sender": "coach", "message": resp.content})

if st.session_state.user_data["uploaded_file"] is None:
    uploaded_file = st.file_uploader("Upload Transaction Ledger (CSV/XLSX):", type=["csv","xlsx"])
    if uploaded_file is not None:
        st.session_state.user_data["uploaded_file"] = uploaded_file
        agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} The user uploaded the file. Celebrate verbosely and ask for the target goal amount.")
        resp = agent.run("Acknowledge file.")
        st.session_state.chat_history.append({"sender": "coach", "message": resp.content})
        st.rerun()

user_input = st.chat_input("Type here...")

if user_input:
    st.session_state.chat_history.append({"sender": "user", "message": user_input})
    user_data = st.session_state.user_data
    input_val = user_input.replace(',', '').replace('$', '').strip()
    
    q_agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} You are gathering data. Be extremely verbose, persona-consistent, and engaging.")

    if user_data["goal_amount"] is None:
        if input_val.replace('.', '', 1).isdigit():
            user_data["goal_amount"] = float(input_val)
            resp = q_agent.run(f"User set goal to ${input_val}. Celebrate this in character and ask how many months they have.")
            response = resp.content
        else: response = "I need a numeric value for the target amount, my friend!"
    elif user_data["goal_months"] is None:
        if input_val.isdigit():
            user_data["goal_months"] = int(input_val)
            resp = q_agent.run(f"Timeframe is {input_val} months. Ask for their monthly net income in character.")
            response = resp.content
        else: response = "Please specify the duration in months as a number."
    elif user_data["monthly_salary"] is None:
        if input_val.replace('.', '', 1).isdigit():
            user_data["monthly_salary"] = float(input_val)
            response = "Mathematical parameters locked. Synthesizing exhaustive financial intelligence report..."
        else: response = "I need your monthly income figure to finalize the baseline."
    else:
        user_data["report_generated"] = False
        response = "Recalculating all financial models with new context..."

    st.session_state.chat_history.append({"sender": "coach", "message": response})
    st.rerun()

if st.session_state.user_data["viz_data"]:
    vd = st.session_state.user_data["viz_data"]
    st.subheader("Critical Financial Visuals 📊")
    m1, m2, m3 = st.columns(3)
    m1.metric("Savings Rate", f"{vd['rate']:.1f}%")
    m2.metric("Monthly Savings", f"${vd['sav']:,.2f}")
    m3.metric("Goal Shortfall Gap", f"${vd['gap']:,.2f}")
    c1, c2 = st.columns(2)
    c1.write("**Top Expenditure Categories**")
    c1.bar_chart(vd['top_df'])
    c2.write("**Goal Savings Projection**")
    c2.line_chart(vd['proj_df'])
    st.divider()

for entry in st.session_state.chat_history:
    with st.chat_message("user" if entry["sender"] == "user" else "assistant"):
        st.markdown(entry["message"])

user_data = st.session_state.user_data
if all([user_data["uploaded_file"], user_data["goal_amount"], user_data["goal_months"], user_data["monthly_salary"]]) and not user_data["report_generated"]:
    if user_data["uploaded_file"].name.endswith(".csv"):
        df = pd.read_csv(user_data["uploaded_file"])
    else:
        xl = pd.ExcelFile(user_data["uploaded_file"])
        df = xl.parse(xl.sheet_names[0])
    
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    cols = [str(c).lower() for c in df.columns]
    date_k, amt_k, cat_k = ['date', 'time', 'day'], ['amount', 'value', 'cost', 'price', 'outflow'], ['category', 'merchant', 'description']
    date_col = next((df.columns[i] for i, c in enumerate(cols) if any(k in c for k in date_k)), None)
    amt_col = next((df.columns[i] for i, c in enumerate(cols) if any(k in c for k in amt_k)), None)
    cat_col = next((df.columns[i] for i, c in enumerate(cols) if any(k in c for k in cat_k)), None)

    if date_col: df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    if amt_col: df[amt_col] = pd.to_numeric(df[amt_col], errors='coerce').abs()
    df = df.dropna(subset=[amt_col, cat_col])

    df_recent = df[df[date_col] >= (datetime.now() - timedelta(days=60))] if date_col else df
    monthly_spending = df_recent.groupby(df_recent[date_col].dt.to_period('M'))[amt_col].sum().mean() if date_col else df_recent[amt_col].sum() / 2
    monthly_savings = max(user_data["monthly_salary"] - monthly_spending, 0)
    required_monthly = user_data["goal_amount"] / user_data["goal_months"]
    savings_gap = max(required_monthly - monthly_savings, 0)
    
    top_cats = df_recent.groupby(cat_col)[amt_col].sum().sort_values(ascending=False).head(15).to_dict()
    recurring = df_recent.groupby([cat_col, amt_col]).size().reset_index(name='count')
    recurring_dict = recurring[recurring['count'] > 1].to_dict('records')
    
    top_df = pd.DataFrame(list(top_cats.items()), columns=['Category', 'Amount']).set_index('Category')
    proj_df = pd.DataFrame({"Month": range(1, user_data["goal_months"] + 1), "Goal Pace": [required_monthly * i for i in range(1, user_data["goal_months"] + 1)], "Current Pace": [monthly_savings * i for i in range(1, user_data["goal_months"] + 1)]}).set_index("Month")
    user_data["viz_data"] = {"rate": (monthly_savings/user_data["monthly_salary"]*100), "sav": monthly_savings, "spend": monthly_spending, "gap": savings_gap, "top_df": top_df, "proj_df": proj_df}

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
- REQUIRED MONTHLY SAVINGS: ${required_monthly:,.2f}
- ACTUAL MONTHLY SAVINGS: ${monthly_savings:,.2f}
- MONTHLY SAVINGS GAP: ${savings_gap:,.2f}

CORE MISSION (BE EXTREMELY VERBOSE, DETAILED, AND ANALYTICAL):
1. EXECUTIVE FINANCIAL HEALTH AUDIT:
   - Provide a 'Health Grade' (A+ to F).
   - Evaluate the objective feasibility of reaching ${user_data['goal_amount']:.2f} in {user_data['goal_months']} months based on current velocity.
   - Use bold headers and professional summaries.

2. QUANTITATIVE PROJECTION & FORECASTING:
   - Create a detailed month-by-month projection table for the next {user_data['goal_months']} months based on ACTUAL savings.
   - Highlight the 'Savings Gap'—the exact amount needed to increase monthly savings to hit the goal early.

3. SUBSCRIPTION & "GRAY CHARGE" DETECTOR:
   - Identify all recurring subscriptions, forgotten free trials, and converted paid services from: {recurring_dict}.
   - Present them in a single, clean list with identified annual costs.

4. SPENDING LEAKAGE & ANOMALY DETECTION:
   - Perform a deep-dive into the top 5 categories. Flag anything exceeding 15% of income.
   - Contrast spending against the 50/30/20 rule of thumb.

5. RISK ASSESSMENT & STRESS TEST:
   - Simulate an 'Emergency Scenario' (e.g., a 15% income drop or a $1,500 surprise expense). 
   - Show how this event shifts the goal timeline.

6. THREE-TIER STRATEGIC ROADMAP:
   - Tier 1: Aggressive. Tier 2: Balanced. Tier 3: Defensive.

7. PERSONA-DRIVEN CLOSING & INTERACTION:
   - Ask a highly sophisticated, verbose question based on your persona to provoke deeper user thought.
   - Respond directly to the user's last message: {st.session_state.chat_history[-2]['message'] if len(st.session_state.chat_history) > 1 else 'None'}.

OUTPUT FORMATTING: Use Markdown only. Complex tables, bold callouts, and blockquotes for emphasis. Ensure tone remains 100% consistent with {selected_voice}.
"""
    )
    report = financial_agent.run(st.session_state.chat_history[-2]["message"] if len(st.session_state.chat_history) > 1 else "Initial Full Intelligence Report Request")
    st.session_state.chat_history.append({"sender": "coach", "message": report.content})
    user_data["report_generated"] = True
    st.rerun()