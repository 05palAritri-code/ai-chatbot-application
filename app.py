from front import show_app, show_auth
import streamlit as st
import os

if hasattr(st, "secrets"):
    for key, value in st.secrets.items():
        os.environ[key] = str(value)

        
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_auth()
else:
    show_app()
