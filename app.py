from front import show_app, show_auth
import streamlit as st
import os
from front_utils import restore_session
try:
    for key, value in st.secrets.items():
        os.environ[key] = str(value)
except Exception:
    pass

restore_session() 

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False

if not st.session_state.get("logged_in", False):
    show_auth()
else:
    show_app()


