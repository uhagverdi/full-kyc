import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import requests
import pytesseract
import cv2
import time
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
from fuzzywuzzy import fuzz
from sqlalchemy import create_engine

# ✅ **Step 1: Setup Secure Database**
DB_FILE = "kyc_onboarding_system.db"
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

# ✅ **Step 2: Configure Sanctions & PEP Screening API**
SANCTIONS_API = "https://api.sanctionslist.com/check"
API_KEY = "your_api_key"

# ✅ **Step 3: Streamlit UI for Client Onboarding**
st.set_page_config(page_title="BlockTech KYC Onboarding", layout="wide")
st.title("📋 BlockTech KYC & Onboarding System")

# ✅ **Step 4: Upload Documents (Passport, ID)**
st.subheader("📂 Upload Your Identity Documents")
uploaded_file = st.file_uploader("Upload Passport/ID (JPG/PNG)", type=["jpg", "png"])

if uploaded_file:
    st.success("✅ Document uploaded successfully!")

    # Convert uploaded file into OpenCV image format
    image = Image.open(uploaded_file)
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # ✅ **Step 5: Extract Text from Document using OCR**
    st.subheader("🔍 Extracting Text from ID Document...")
    extracted_text = pytesseract.image_to_string(image)
    st.write(extracted_text)

    # Extract Name & Date of Birth (Basic Parsing)
    lines = extracted_text.split("\n")
    client_name = lines[0].strip() if len(lines) > 0 else "Unknown"
    dob = lines[1].strip() if len(lines) > 1 else "Unknown"

    st.write(f"**Detected Name:** {client_name}")
    st.write(f"**Detected Date of Birth:** {dob}")

    # ✅ **Step 6: Sanctions & PEP Screening**
    st.subheader("⚠️ Performing Sanctions & PEP Screening")
    def check_sanctions(name):
        response = requests.post(SANCTIONS_API, json={"name": name}, headers={"Authorization": f"Bearer {API_KEY}"})
        if response.status_code == 200:
            return response.json().get("match_found", False)
        return False

    sanctions_flag = check_sanctions(client_name)
    if sanctions_flag:
        st.error("🚨 Client appears on a sanctions/PEP list. Further review needed!")
    else:
        st.success("✅ No matches found in sanctions/PEP databases.")

    # ✅ **Step 7: Risk-Based KYC Scoring**
    st.subheader("📊 Risk Scoring Model")
    risk_score = 0
    if sanctions_flag:
        risk_score += 50
    if "Unknown" in [client_name, dob]:
        risk_score += 30
    if np.random.rand() > 0.8:  # Simulating additional risk rules
        risk_score += 20

    risk_level = "Low"
    if risk_score > 50:
        risk_level = "High"
    elif risk_score > 20:
        risk_level = "Medium"

    st.write(f"**Computed Risk Score:** {risk_score} (Level: {risk_level})")

    # ✅ **Step 8: Approval & Compliance Logs**
    st.subheader("📝 Decision & Compliance Logging")
    decision = "Approve"
    if risk_level == "High":
        decision = "Review Manually"
    elif risk_level == "Medium":
        decision = "Enhanced Due Diligence (EDD)"
    
    st.write(f"**Final Decision:** {decision}")

    # Store in database
    with engine.begin() as conn:
        pd.DataFrame([{
            "Client_Name": client_name,
            "Date_Of_Birth": dob,
            "Risk_Score": risk_score,
            "Risk_Level": risk_level,
            "Decision": decision,
            "Timestamp": datetime.now()
        }]).to_sql("kyc_cases", conn, if_exists="append", index=False)

    st.success("✅ KYC case successfully logged!")

