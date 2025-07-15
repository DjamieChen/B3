# --- IMPORTS ---
import streamlit as st
import json
import os
import re
import ast
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# --- AUTHORIZED MEMBERS ---
MEMBERS = {
    "jamie": "5104014506",
    "jacquelyn": "5104014500",
    "aprajit": "3413457264"
}

# --- CONFIG ---
DB_DIR = "email_histories"
CONTACTS_FILE = "contacts.json"
B3_ADDRESS = "B3investors@gmail.com"
os.makedirs(DB_DIR, exist_ok=True)

# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="📬 B3 Leasing Email Generator", layout="centered")
st.title("📬 B3 Leasing Email Generator")

# --- MEMBER AUTHENTICATION ---
st.subheader("🔐 Member Login")
username = st.text_input("Enter your name:")
phone_val = st.text_input("Enter your phone number:")

def is_member(username, phone_val):
    return username in MEMBERS and MEMBERS[username] == phone_val

if username and phone_val:
    if is_member(username.lower(), phone_val):
        st.success(f"Welcome, {username.capitalize()}!")

        # --- Load Contact Database ---
        def load_contacts():
            if os.path.exists(CONTACTS_FILE):
                with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}

        def save_contacts(contacts):
            with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
                json.dump(contacts, f, indent=2)

        contacts = load_contacts()

        st.markdown("### 📇 Contact Info")
        contact_email = st.text_input("Enter contact's email")

        if contact_email and "@" in contact_email:
            existing = contact_email in contacts

            if existing:
                contact = contacts[contact_email]
                st.success("✅ Contact found in system.")

                contact_name = contact.get("name", "")
                contact_phone = contact.get("phone", "")
                company = contact.get("company", "")
                industry = contact.get("industry", "")

                st.write(f"**Name:** {contact_name}")
                st.write(f"**Phone:** {contact_phone}")
                st.write(f"**Company:** {company}")
                st.write(f"**Industry:** {industry}")
                st.info("Fields auto-filled from contact database.")

                # 👉 You can proceed to email prompt & generation here

            else:
                st.warning("🆕 New contact. Please add info.")
                contact_name = st.text_input("Contact's Full Name")
                contact_phone = st.text_input("Contact's Phone Number")
                company = st.text_input("Company Name")
                industry = st.text_input("Industry")

                if contact_name and contact_phone and company and industry:
                    contacts[contact_email] = {
                        "name": contact_name,
                        "phone": contact_phone,
                        "company": company,
                        "industry": industry
                    }
                    save_contacts(contacts)
                    st.success("💾 Contact saved successfully!")
                    st.experimental_rerun()
        else:
            st.info("✉️ Please enter a valid contact email to continue.")
    else:
        st.error("Access denied. Invalid credentials.")
