import os
import sys

# Inject subdirectories into sys.path to enable imports without changing page source files
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
for subdir in ["views", "helpers", "services"]:
    path = os.path.join(base_dir, subdir)
    if path not in sys.path:
        sys.path.insert(0, path)

import streamlit as st

import chatbot_page
import dashboard_page
import home_page
import prediction_page
import reports_page
import suggestions_page
import upload_page
from utils import apply_custom_styling, initialize_session_state, render_sidebar


st.set_page_config(
    page_title="DataVision",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styling()
initialize_session_state()

selected_page = render_sidebar()

if selected_page == "home":
    home_page.main()
elif selected_page == "upload":
    upload_page.main()
elif selected_page == "dashboard":
    dashboard_page.main()
elif selected_page == "chatbot":
    chatbot_page.main()
elif selected_page == "prediction":
    prediction_page.main()
elif selected_page == "suggestions":
    suggestions_page.main()
elif selected_page == "reports":
    reports_page.main()
