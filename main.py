import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from agno.agent import Agent
from agno.models.groq import Groq
import os
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = Groq(api_key=GROQ_API_KEY, id="llama-3.1-8b-instant")

st.set_page_config(page_title="Elite Financial Intelligence Coach", layout="wide")
st.title("Elite Financial Intelligence Coach 💬")

voices = {
    "Conservative Advisor": "You are a disciplined, risk-averse Wealth Protector. Your tone is professional and stern. Focus on capital preservation and mathematical certainty.",
    "Fun Saver": "You are a high-energy Financial Buddy. Your philosophy is 'Save Hard, Play Hard.' Use emojis and humor to encourage the user. Be verbose but mathematically accurate.",
    "Analytical Guru": "You are a meticulous Quantitative Strategist. You provide deep-dive insights into categorical anomalies and spending velocities with surgical precision."
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
        "viz_data": None,
        "full_report_text": ""
    }

if "last_voice" not in st.session_state:
    st.session_state.last_voice = selected_voice

if st.session_state.last_voice != selected_voice:
    st.session_state.chat_history = []
    st.session_state.user_data = {k: None for k in st.session_state.user_data}
    st.session_state.last_voice = selected_voice

if not st.session_state.chat_history:
    agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} Greet the user with a short-length,concise, persona-rich introduction and request the transaction file.")
    resp = agent.run("Introduce yourself.")
    st.session_state.chat_history.append({"sender": "coach", "message": resp.content})

with st.sidebar:
    st.header("Financial Dashboard 📈")
    if st.session_state.user_data["viz_data"]:
        vd = st.session_state.user_data["viz_data"]
        st.metric("Savings Rate", f"{vd['rate']:.1f}%")
        st.metric("Monthly Savings", f"${vd['sav']:,.2f}")
        st.metric("Monthly Gap", f"${vd['gap']:,.2f}")
        st.write("**Top Spending (90 Days)**")
        st.bar_chart(vd['top_df'])
        st.write("**Savings Projection**")
        st.line_chart(vd['proj_df'])
        
        if st.session_state.user_data["full_report_text"]:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=11)
            pdf.cell(200, 10, txt=f"Financial Intelligence Audit - {selected_voice}", ln=1, align='C')
            pdf.ln(10)
            pdf.multi_cell(0, 10, txt=st.session_state.user_data["full_report_text"].encode('latin-1', 'replace').decode('latin-1'))
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(label="📥 Download Audit PDF", data=pdf_output, file_name="Financial_Audit.pdf", mime="application/pdf")
    else:
        st.info("Upload data and set goals to see visualizations.")

if st.session_state.user_data["uploaded_file"] is None:
    uploaded_file = st.file_uploader("Upload Transaction Ledger (CSV/XLSX):", type=["csv","xlsx"])
    if uploaded_file is not None:
        st.session_state.user_data["uploaded_file"] = uploaded_file
        agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} Acknowledge file briefly and ask for the target savings goal.")
        resp = agent.run("Acknowledge file.")
        st.session_state.chat_history.append({"sender": "coach", "message": resp.content})
        st.rerun()

user_input = st.chat_input("Type here...")

if user_input:
    st.session_state.chat_history.append({"sender": "user", "message": user_input})
    user_data = st.session_state.user_data
    
    clean_input = user_input.replace(',', '').lower()
    found_numbers = re.findall(r'\d+(?:\.\d+)?', clean_input)
    is_years = "year" in clean_input

    q_agent = Agent(model=llm, instructions=f"You are the {selected_voice}. {voices[selected_voice]} Gathering parameters for a mathematical budget audit. Keep responses short and persona-consistent.")

    if user_data["goal_amount"] is None:
        if found_numbers:
            user_data["goal_amount"] = float(found_numbers[0])
            if len(found_numbers) > 1:
                val = float(found_numbers[1])
                user_data["goal_months"] = int(val * 12) if is_years else int(val)
                resp = q_agent.run(f"Goal: ${user_data['goal_amount']} over {user_data['goal_months']} months. Ask for monthly income.")
            else:
                resp = q_agent.run(f"Goal: ${user_data['goal_amount']}. Ask for the timeframe (months or years).")
            response = resp.content
        else: response = "State the numeric target goal amount."
    elif user_data["goal_months"] is None:
        if found_numbers:
            val = float(found_numbers[0])
            user_data["goal_months"] = int(val * 12) if is_years else int(val)
            resp = q_agent.run(f"Temporal horizon: {user_data['goal_months']} months. Ask for monthly income.")
            response = resp.content
        else: response = "Specify the duration in numeric form."
    elif user_data["monthly_salary"] is None:
        if found_numbers:
            user_data["monthly_salary"] = float(found_numbers[0])
            response = "Parameters locked. Commencing multi-dimensional financial audit..."
        else: response = "I need net income data to finalize the models."
    else:
        user_data["report_generated"] = False
        response = "Recalculating predictive models..."

    st.session_state.chat_history.append({"sender": "coach", "message": response})
    st.rerun()

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

    df_recent = df[df[date_col] >= (datetime.now() - timedelta(days=90))] if date_col else df
    monthly_spending = df_recent.groupby(df_recent[date_col].dt.to_period('M'))[amt_col].sum().mean() if date_col else df_recent[amt_col].sum() / 3
    monthly_savings = max(user_data["monthly_salary"] - monthly_spending, 0)
    required_monthly = user_data["goal_amount"] / user_data["goal_months"]
    savings_gap = max(required_monthly - monthly_savings, 0)
    
    top_cats = df_recent.groupby(cat_col)[amt_col].sum().sort_values(ascending=False).head(15).to_dict()
    recurring = df_recent.groupby([cat_col, amt_col]).size().reset_index(name='count')
    recurring_dict = recurring[recurring['count'] > 1].to_dict('records')
    
    top_df = pd.DataFrame(list(top_cats.items()), columns=['Category', 'Amount']).set_index('Category')
    proj_df = pd.DataFrame({"Month": range(1, user_data["goal_months"] + 1), "Goal": [required_monthly * i for i in range(1, user_data["goal_months"] + 1)], "Current": [monthly_savings * i for i in range(1, user_data["goal_months"] + 1)]}).set_index("Month")
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
- ACTUAL MONTHLY SAVINGS (90-DAY AVG): ${monthly_savings:,.2f}
- MONTHLY SAVINGS GAP: ${savings_gap:,.2f}

CORE MISSION (BE EXTREMELY VERBOSE, DETAILED, AND ANALYTICAL):
1. THE STATE OF YOUR CAPITAL (Audit):
   - Provide a 'Health Grade' (A+ to F).
   - Evaluate objective feasibility based on ACTUAL velocity.
   - Use bold headers and persona-consistent language. NO GENERIC HEADERS.

2. QUANTITATIVE PROJECTION & FORECASTING:
   - Create a detailed month-by-month projection table for the next {user_data['goal_months']} months based on ACTUAL savings.
   - Highlight the 'Savings Gap' needed to reach the goal.

3. RECURRING LIABILITIES & LEAKAGE (Gray Charges):
   - Identify all recurring subscriptions from: {recurring_dict}. 
   - Present annual impact.

4. CATEGORICAL ANOMALIES (Spending Audit):
   - Deep-dive into {top_cats}. Compare spending against the 50/30/20 rule.
   - Flag any category that exceeds its mathematical utility.

5. FISCAL STRESS TEST:
   - Simulate a one-time $1,500 emergency expense. 
   - Show how this single event impacts the final target date mathematically.

6. STRATEGIC ROADMAPS (Aggressive, Balanced, Defensive):
   - Provide three tiered strategies for capital preservation.

7. TACTICAL INTERVENTIONS:
   - Provide 5-7 HIGHLY SPECIFIC suggestions based on the data in {top_cats}. 
   - For example: cap 'Movies' at a specific dollar amount, or negotiate the 'Internet' bill.

8. PERSONA-DRIVEN CLOSING & INTERACTION:
   - Ask a highly sophisticated, verbose question.
   - Respond directly to: {st.session_state.chat_history[-2]['message'] if len(st.session_state.chat_history) > 1 else 'None'}.

OUTPUT FORMATTING: Use Markdown only. Complex tables, bold callouts, and blockquotes. NO SYSTEM HEADERS like "RISK ASSESSMENT".
"""
    )
    report = financial_agent.run(st.session_state.chat_history[-2]["message"] if len(st.session_state.chat_history) > 1 else "Initial Full Intelligence Report Request")
    st.session_state.chat_history.append({"sender": "coach", "message": report.content})
    st.session_state.user_data["full_report_text"] = report.content
    user_data["report_generated"] = True
    st.rerun()