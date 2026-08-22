import streamlit as st
import requests

# Page setup
st.set_page_config(page_title="AI DevOps Dashboard", layout="wide")
st.title("🚨 AI System Alerts Dashboard (Member 4)")
st.write("Live data streaming from Member 1 -> Member 2 -> AI (Member 3) -> Here!")

try:
    # Fetch data from Member 2 Backend
    response = requests.get("http://localhost:8000/logs")
    data = response.json()
    
    if data.get("total_events", 0) > 0:
        st.success(f"✅ Live Connection Active! Total Events Analyzed: {data['total_events']}")
        st.markdown("---")
        
        # Display each event
        for event in data["events"]:
            score = event.get('ai_score', 0)
            
            # Color code based on AI Severity Score
            if score >= 8:
                st.error(f"🔥 CRITICAL (Score: {score}/10) | Source: {event['source']}")
            elif score >= 5:
                st.warning(f"⚠️ WARNING (Score: {score}/10) | Source: {event['source']}")
            else:
                st.info(f"✅ LOW PRIORITY (Score: {score}/10) | Source: {event['source']}")
            
            st.write(f"**🔴 Original Error:** {event['description']}")
            st.write(f"**🤖 AI Action Plan:** {event.get('ai_explanation', 'No explanation')}")
            st.markdown("---")
    else:
        st.warning("⚠️ No data found! Make sure Member 1's ingestion script is running.")
except Exception as e:
    st.error("❌ ERROR: Cannot connect to Backend. Make sure Member 2 server is running!")