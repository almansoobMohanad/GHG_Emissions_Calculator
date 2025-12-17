"""
Header component for authentication page
"""
import streamlit as st


def render_header():
    """Render welcome section with app title and description."""
    st.title("🌱 GHG Emissions Calculator")
    st.markdown("### Track, Manage, and Report Your Carbon Footprint")
    st.markdown("A comprehensive platform for managing greenhouse gas emissions across all three scopes.")
    st.divider()