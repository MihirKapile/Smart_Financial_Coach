import plotly.express as px
import streamlit as st

def generate_spending_chart(data_dict, chart_type="pie"):
    """
    Called by the agent to render a chart in the UI.
    data_dict: list of dicts [{'category': 'Coffee', 'amount': 120}, ...]
    """
    import pandas as pd
    df = pd.DataFrame(data_dict)
    
    if chart_type == "pie":
        fig = px.pie(df, values='amount', names='category', title="Spending Distribution", hole=0.4)
    else:
        fig = px.bar(df, x='category', y='amount', title="Monthly Spending by Category")
        
    st.plotly_chart(fig, use_container_width=True)
    return "Chart successfully rendered in the UI."