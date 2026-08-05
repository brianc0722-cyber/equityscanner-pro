import streamlit as st
import os
import requests
from datetime import datetime

st.set_page_config(page_title="EquityScanner Pro", page_icon="📈", layout="wide")

st.title("📈 EquityScanner Pro")
st.caption("Real-time Stock Scanner + Pre-Market Analytics")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.write("**API Base URL:**", API_BASE)

# Health check
try:
    r = requests.get(f"{API_BASE}/health", timeout=6)
    if r.status_code == 200:
        st.success("✅ Backend connected")
        st.json(r.json())
    else:
        st.warning("⚠️ Backend returned error")
except Exception as e:
    st.error(f"Backend not reachable: {e}")

st.divider()

st.subheader("Quick Demo")
ticker = st.selectbox("Ticker", ["AAPL", "NVDA", "TSLA", "MSFT"])

c1, c2, c3 = st.columns(3)
c1.metric("Relative Volume", "2.65x")
c2.metric("Gap", "+1.45%")
c3.metric("Direction", "UP")

if st.button("🚀 Run Demo"):
    st.success(f"Demo prediction for {ticker}: **BULLISH** (68% confidence)")

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
