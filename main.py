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

st.set_page_config(page_title="Smart Financial Coach Chat", layout="wide")
st.title("Smart Financial Coach 💬")

voices = {
    "Conservative Advisor": """
Focus on safety, long-term planning, and disciplined budgeting. 
Highlight risks and emphasize security over enjoyment. 
Give professional, serious advice with concrete steps.
""",
    "Fun Saver": """
Encourage enjoyment while saving. Be playful, motivational, and cheerful.
Use jokes, analogies, emojis, and fun commentary.
Give actionable advice without making the user feel guilty.
""",
    "Analytical Guru": """
Give precise, data-driven insights. Focus on numbers, trends, anomalies, and forecasts.
Use charts, percentages, and comparisons. Tone is professional, analytical, and methodical.
"""
}

intro_messages = {
    "Conservative Advisor": (
        "Hello! I'm your cautious financial guide. 📊\n\n"
        "My goal is to help you plan safely, understand your spending habits, and reach your financial goals with minimal risk. "
        "We'll go step by step, ensuring your plan is secure and disciplined.\n\n"
        "First, please upload your transactions file (CSV or Excel) so I can analyze your spending history."
    ),
    "Fun Saver": (
        "Hey there! 🎉 I'm your fun financial buddy!\n\n"
        "I love helping you save while still enjoying life. "
        "We'll look at your spending, find ways to save some money without missing out on the fun, "
        "and even spot sneaky subscriptions that might be draining your wallet. 😎\n\n"
        "Let's start with your transactions file (CSV or Excel) so I can see where your money is going!"
    ),
    "Analytical Guru": (
        "Greetings! 📈 I'm your analytical financial expert.\n\n"
        "I will examine your spending patterns, detect anomalies, and provide precise insights to optimize your savings. "
        "We'll work with numbers, trends, and forecasts to ensure you're on track.\n\n"
        "Please upload your transactions file (CSV or Excel) to begin our analysis."
    )
}

guided_questions = {
    "Conservative Advisor": [
        "What is your financial goal amount? (e.g., 3000)",
        "In how many months would you like to reach this goal?",
        "What is your monthly income?"
    ],
    "Fun Saver": [
        "What's your money goal? (Tell me the amount you want to save!) 💰",
        "How many months do we have to reach this goal? ⏳",
        "And what's your monthly income? Let's see how much we can have fun while saving!"
    ],
    "Analytical Guru": [
        "Please provide your financial goal amount.",
        "Specify the timeframe in months to reach this goal.",
        "Enter your monthly salary so I can calculate savings rate and projections."
    ]
}

selected_voice = st.selectbox("Choose Advisor Voice", list(voices.keys()))

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
        "current_question": 0
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
        "report_generated": False,
        "current_question": 0
    }
    st.session_state.last_voice = selected_voice

if not st.session_state.chat_history:
    st.session_state.chat_history.append({
        "sender": "coach",
        "message": intro_messages[selected_voice]
    })

if st.session_state.user_data["uploaded_file"] is None:
    uploaded_file = st.file_uploader("Upload your transactions file (CSV/XLSX):", type=["csv","xlsx"])
    if uploaded_file is not None:
        st.session_state.user_data["uploaded_file"] = uploaded_file
        if not st.session_state.user_data["file_uploaded_message_added"]:
            st.session_state.chat_history.append({
                "sender": "coach",
                "message": "File uploaded successfully! " + guided_questions[selected_voice][0]
            })
            st.session_state.user_data["file_uploaded_message_added"] = True
            st.rerun()

user_input = st.chat_input("Type your message here:")

if user_input:
    st.session_state.chat_history.append({"sender": "user", "message": user_input})
    user_data = st.session_state.user_data
    response = ""
    input_val = user_input.replace(',', '').replace('$', '').strip()

    if "salary" in user_input.lower() or "income" in user_input.lower():
        digits = "".join(filter(str.isdigit, user_input))
        if digits: user_data["monthly_salary"] = float(digits)
    
    if "goal" in user_input.lower() and "month" not in user_input.lower():
        digits = "".join(filter(str.isdigit, user_input))
        if digits: user_data["goal_amount"] = float(digits)

    if user_data["uploaded_file"] is None:
        response = "Please upload your transactions file before we continue."
    elif user_data["goal_amount"] is None:
        if input_val.replace('.', '', 1).isdigit():
            user_data["goal_amount"] = float(input_val)
            response = guided_questions[selected_voice][1]
        else:
            response = "I need a number for your goal. " + guided_questions[selected_voice][0]
    elif user_data["goal_months"] is None:
        if input_val.isdigit():
            user_data["goal_months"] = int(input_val)
            response = guided_questions[selected_voice][2]
        else:
            response = "I need to know the number of months. " + guided_questions[selected_voice][1]
    elif user_data["monthly_salary"] is None:
        if input_val.replace('.', '', 1).isdigit():
            user_data["monthly_salary"] = float(input_val)
            response = "Great! All information is collected. I will now generate your report."
        else:
            response = "I need a number for your income. " + guided_questions[selected_voice][2]
    else:
        user_data["report_generated"] = False
        response = "Thinking..."

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
        df = pd.read_excel(user_data["uploaded_file"])

    column_names = df.columns
    date_col = next((c for c in column_names if "date" in c.lower()), None)
    amount_col = next((c for c in column_names if "amount" in c.lower()), None)
    category_col = next((c for c in column_names if "category" in c.lower() or "merchant" in c.lower()), None)

    if date_col: df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    if amount_col: df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    df = df.dropna(subset=[amount_col, category_col])

    recent_days = 60
    if date_col:
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        df_recent = df[df[date_col] >= cutoff_date]
        df_recent['month'] = df_recent[date_col].dt.to_period('M')
        monthly_spending = df_recent.groupby('month')[amount_col].sum().mean()
    else:
        df_recent = df
        monthly_spending = df_recent[amount_col].sum() / (recent_days/30)

    monthly_savings = max(user_data["monthly_salary"] - monthly_spending, 0)
    savings_rate = (monthly_savings / user_data["monthly_salary"] * 100) if user_data["monthly_salary"] > 0 else 0
    total_spent = df_recent[amount_col].sum()
    recurring = df_recent.groupby([category_col, amount_col]).size().reset_index(name='count')
    recurring = recurring[recurring['count'] > 1]
    gray_charges = df_recent[df_recent[amount_col] < user_data["monthly_salary"]*0.05]
    gray_charges = gray_charges.groupby([category_col, amount_col]).size().reset_index(name='count')
    gray_charges = gray_charges[gray_charges['count'] > 1]
    top_categories = df_recent.groupby(category_col)[amount_col].sum().sort_values(ascending=False).head(5)

    financial_agent = Agent(
        name="Full Financial Advisor",
        model=llm,
        instructions=f"""
You are a {selected_voice} financial advisor.
{voices[selected_voice]}

Structured data:
- Total spent last {recent_days} days: ${total_spent:.2f}
- Average monthly spending: ${monthly_spending:.2f}
- Monthly salary: ${user_data['monthly_salary']:.2f}
- Monthly savings: ${monthly_savings:.2f} ({savings_rate:.1f}% savings rate)
- Goal: ${user_data['goal_amount']:.2f} in {user_data['goal_months']} months
- Top categories: {top_categories.to_dict()}
- Recurring subscriptions: {recurring.to_dict()}
- Gray charges: {gray_charges.to_dict()}

Current User Query: {st.session_state.chat_history[-2]['message'] if len(st.session_state.chat_history) > 1 else 'None'}

Tasks:
1. Personalized Goal Forecasting:
   - Are they on track to reach their goal? Show months remaining.
   - Provide actionable steps and "what-if" scenarios: cancel subscriptions, cut overspending categories.

2. Subscription & Gray Charge Detector:
   - Detect all recurring and forgotten charges.
   - Show potential savings if canceled.

3. Category-wise Spending Analysis:
   - Highlight top spending categories.
   - Detect anomalies or sudden spikes.

4. Actionable Recommendations:
   - Step-by-step tips to optimize savings.
   - Persona-specific motivational advice.

5. Interaction:
   - YOU MUST ANSWER THE USER'S SPECIFIC QUERY DIRECTLY AT THE VERY BEGINNING OF YOUR RESPONSE.
   - Then, provide the dynamic what-if simulations and the full report analysis below it.

6. Output:
   - Respond strictly in Markdown.
   - Include tables, bullet points, percentages, and forecasts.
   - Make report in-depth and persona-consistent.
"""
    )

    report = financial_agent.run(st.session_state.chat_history[-2]['message'] if len(st.session_state.chat_history) > 1 else "Generate full report")
    st.session_state.chat_history.append({"sender": "coach", "message": report.content if hasattr(report, "content") else report})
    user_data["report_generated"] = True
    st.rerun()