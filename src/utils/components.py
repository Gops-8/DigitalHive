# components.py
import streamlit as st
import pandas as pd
import plotly.express as px

import streamlit as st

class Components:
    def __init__(self):
        pass

    def show_login(self):
        st.title("🔐 Login")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if username == "admin" and password == "password":
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
        
        csv = df.to_csv(index=False)
        st.download_button(
            "Download Results",
            csv,
            "analysis_results.csv",
            "text/csv"
        )
