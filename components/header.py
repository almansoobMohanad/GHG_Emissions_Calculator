"""
Header component for authentication page
"""
import streamlit as st


def render_header():
    """Render welcome section with app title and description."""
    st.title("🌱 Sustainability Monitoring Hub")
    st.markdown("### Track, Manage, and Report Your Sustainability Journey")
    st.markdown("A comprehensive platform to monitor GHG emissions, complete compliance forms (SEDG), and track reduction goals with actionable roadmaps.")
    st.divider()