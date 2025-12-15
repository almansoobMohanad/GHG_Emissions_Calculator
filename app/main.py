import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database, get_emissions_summary

st.set_page_config(page_title="GHG Calculator", layout="wide")

def main():
    st.title("🌱 GHG Emissions Calculator")
    
    # Test database connection
    db = get_database()
    if db.connect():
        st.success("✅ Database connected!")
        db.disconnect()
    else:
        st.error("❌ Database connection failed")
    
    # Test caching
    if st.button("Test Cache"):
        summary = get_emissions_summary(1, "2024")
        st.json(summary)

if __name__ == "__main__":
    main()