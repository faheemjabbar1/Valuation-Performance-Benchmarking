import streamlit as st
import pandas as pd

st.set_page_config(page_title="Peer Comparison", layout="wide")
st.title("Peer Comparison Dashboard (Stub)")

st.info("Run the pipeline first to generate 'reports/peer_comparison.xlsx'. Then point this app to the output.")

uploaded = st.file_uploader("Upload the generated Excel report", type=["xlsx"])
if uploaded:
    xls = pd.ExcelFile(uploaded)
    summary = pd.read_excel(xls, "Summary")
    st.subheader("Top Summary")
    st.dataframe(summary)
