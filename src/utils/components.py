import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime  
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
        successful = len(df[df['Status'] == 'success'])
        failed = total - successful

        col1.metric("Total URLs", total)
        col2.metric("Successful", successful)
        col3.metric("Failed", failed)

        sanitized_df = df.copy()
        # Convert object columns to string and fill NaN values with a blank space.
        for column in sanitized_df.columns:
            if sanitized_df[column].dtype == 'object':
                sanitized_df[column] = sanitized_df[column].astype(str)
        sanitized_df = sanitized_df.fillna(' ')

        # Replace numeric zeros with an empty string.
        for col in sanitized_df.select_dtypes(include=['number']).columns:
            sanitized_df[col] = sanitized_df[col].replace(0, '')

        # Remove the default index and add a serial number column starting from 1.
        sanitized_df.reset_index(drop=True, inplace=True)
        sanitized_df.index = sanitized_df.index + 1
        # sanitized_df.insert(0, "Sl No", sanitized_df.index)
        # sanitized_df.drop_index( inplace=True)
        st.dataframe(sanitized_df, use_container_width=True)

