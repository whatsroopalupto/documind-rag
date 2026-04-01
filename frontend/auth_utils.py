import firebase_admin
from firebase_admin import credentials, auth
import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()
# Look for either FIREBASE_WEB_API_KEY or FIREBASE_API_KEY
# (Checks Streamlit Secrets first for cloud deployment, then falls back to local .env)
if hasattr(st, "secrets") and "FIREBASE_API_KEY" in st.secrets:
    FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_API_KEY"]
else:
    FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_API_KEY") or os.getenv("FIREBASE_WEB_API_KEY")

# --- DYNAMIC PATHING (To prevent errors) ---
current_dir = os.path.dirname(__file__)

# Get the filename from .env, default to 'firebase-key.json'
key_filename = os.getenv("FIREBASE_KEY_FILE", "firebase-key.json")
key_path = os.path.join(current_dir, key_filename)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # 1. First, check if deployment secrets exist (Streamlit Cloud)
        if hasattr(st, "secrets") and "firebase" in st.secrets:
            # We convert the secret to a strict standard dictionary to avoid proxy errors
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
        # 2. Otherwise, fall back to the local .json file
        elif os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

def sign_up(email, password, name):
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        st.success("Account created! Please switch to Login.")
        return True
    except Exception as e:
        st.error(f"Sign up failed: {e}")
        return False

def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code == 200:
            st.session_state.logged_in = True
            user_info = auth.get_user_by_email(email)
            st.session_state.user = user_info
            return True
        else:
            st.error("Wrong credentials: Invalid username or password.")
            return False
    except Exception as e:
        st.error(f"Login request failed: {e}")
        return False

def reset_password(email):
    """Sends a secure reset email via Firebase REST API"""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.success(f"A secure reset link has been sent to {email}. Please check your inbox.")
            return True
        else:
            st.error("Could not send reset email. Please ensure the email is correct.")
            return False
    except Exception as e:
        st.error(f"Reset request error: {e}")
        return False