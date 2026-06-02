from front import show_app, show_auth
import streamlit as st

if not st.session_state.logged_in:
    show_auth()
else:
    show_app()
