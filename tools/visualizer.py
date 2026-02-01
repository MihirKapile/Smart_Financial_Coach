import plotly.express as px
import streamlit as st

def generate_spending_chart(data_list, chart_type="pie", title="Financial Breakdown"):
    try:
        import pandas as pd
        import plotly.express as px
        
        df = pd.DataFrame(data_list)
        
        if chart_type == "pie":
            fig = px.pie(df, values='value', names='label', title=title, 
                         hole=0.4, color='label',
                         color_discrete_map={'Essential': '#27ae60', 'Non-Essential': '#e74c3c'})
        else:
            fig = px.bar(df, x='label', y='value', title=title, color='label')

        st.plotly_chart(fig, use_container_width=True)
        
        return f"Successfully rendered {chart_type} chart."
    except Exception as e:
        return f"Tool Error: {str(e)}"