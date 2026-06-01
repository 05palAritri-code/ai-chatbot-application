from front import show_app, show_auth
from streamlit import st

if not st.session_state.logged_in:
    show_auth()
else:
    show_app()
