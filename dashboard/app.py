import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="EquityScanner Pro", page_icon="📈", layout="wide")

st.title("📈 EquityScanner Pro")
st.caption("Real-time Stock Scanner + Pre-Market Analytics")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

def check_backend():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200, r.json()
    except Exception as e:
        return False, {"error": str(e)}

ok, info = check_backend()

if ok:
    st.success(f"✅ Backend connected: {API_BASE}")
    st.json(info)
else:
    st.warning(f"⚠️ Backend not reachable: {API_BASE}")
    st.caption(f"Error: {info.get('error', 'unknown')}")

st.divider()

st.subheader("Quick Demo")

ticker = st.selectbox("Ticker", ["AAPL", "NVDA", "TSLA", "MSFT"])

c1, c2, c3 = st.columns(3)
c1.metric("Relative Volume", "2.65x")
c2.metric("Gap", "+1.45%")
c3.metric("Direction", "UP")

if st.button("🚀 Run Demo"):
    st.success(f"Demo: {ticker} → **BULLISH** (68% confidence)")

st.caption(f"Last check: {datetime.now().strftime('%H:%M:%S')}")
