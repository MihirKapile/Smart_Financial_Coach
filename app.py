import streamlit as st
import os
from tools.knowledge import get_knowledge_base, ingest_data
from agents.orchestrator import get_smart_coach

st.set_page_config(page_title="Smart Finance Coach", layout="wide")

# --- Initialize Session State ---
if "kb" not in st.session_state:
    st.session_state.kb = get_knowledge_base()

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("Groq API Key", type="password")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    
    persona = st.selectbox("Choose Persona", ["Tough Love", "Wealth Architect", "Bestie"])
    
    st.divider()
    st.header("🎯 Goal")
    target = st.number_input("Goal Amount ($)", value=3000)
    months = st.slider("Timeframe (Months)", 1, 24, 10)
    
    st.divider()
    uploaded_file = st.file_uploader("Upload Statement", type=['csv', 'pdf', 'xlsx'])

st.title("💸 AI Smart Financial Coach")

if uploaded_file and api_key:
    temp_dir = "tmp/uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("📥 Index Financial Data"):
        with st.spinner("Agents are reading your files..."):
            file_type = uploaded_file.name.split('.')[-1]
            ingest_data(st.session_state.kb, file_path, file_type)
            st.success("Data indexed in LanceDB!")

    if st.button("🚀 Run AI Financial Audit"):
        coach = get_smart_coach(st.session_state.kb, persona)
        
        with st.status("The AI Team is collaborating...", expanded=True) as status:
            query = (
                f"Analyze my data. Can I save ${target} in {months} months? "
                "List all subscriptions and point out any spending anomalies."
            )
            response = coach.run(query)
            status.update(label="Audit Complete!", state="complete")
        
        st.markdown(response.content)
else:
    st.info("Please provide your API Key and upload a file to start.")