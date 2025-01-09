# components.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime  
import streamlit as st
import uuid

class Components:
    def __init__(self):
        pass

    def show_login(self, auth_manager):
        st.title("🔐 Login")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if auth_manager.verify_credentials(username, password):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")



    def display_results(self, df):
        st.success("Analysis complete!")
        
        col1, col2, col3 = st.columns(3)
        total = len(df)
        successful = len(df[df['status'] == 'success'])
        failed = total - successful
        
        col1.metric("Total URLs", total)
        col2.metric("Successful", successful)
        col3.metric("Failed", failed)
        
        st.dataframe(df)
        
        # Generate a unique key for the download button
        csv = df.to_csv(index=False)
        # unique_key = f"download_results_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        unique_key = f"download_results_{uuid.uuid4()}"
        st.download_button(
            label="Download Results",
            data=csv,
            file_name="analysis_results.csv",
            mime="text/csv",
            key=unique_key
        )

