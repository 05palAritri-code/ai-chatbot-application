from front import show_app, show_auth
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_auth()
else:
    show_app()
