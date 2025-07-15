import json
import os
import re
import ast
from datetime import datetime
import streamlit as st
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# --- CONFIG ---
DB_DIR = "email_histories"
B3_ADDRESS = "B3investors@gmail.com"
CONTACTS_FILE = "contacts.json"
os.makedirs(DB_DIR, exist_ok=True)

# --- Strict Members ---
MEMBERS = {
    "jamie": "5104014506",
    "jacquelyn": "5104014500",
    "aprajit": "3413457264"
}

# --- Contact Info Database ---
def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_contacts(contacts):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2)

# --- File Helpers ---
def get_user_file(username):
    safe_username = username.replace("@", "_at_").replace(".", "_dot_")
    return os.path.join(DB_DIR, f"{safe_username}.json")

def load_db(username):
    user_file = get_user_file(username)
    if not os.path.exists(user_file):
        return []
    with open(user_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(username, history):
    user_file = get_user_file(username)
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def get_context(history):
    return "\n".join([f"{item['role'].capitalize()}: {item['message']}" for item in history])

def clean_response(text):
    try:
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = ast.literal_eval(text)
    except Exception:
        pass
    text = text.replace("{", "").replace("}", "").replace('"', "")
    return re.sub(r'\n{3,}', '\n\n', text).strip()

def get_current_email_date():
    dt = datetime.now()
    return dt.strftime("%A, %B %d, %Y, %#I:%M %p %Z")

# --- Prompt Template ---
prompt_template = """
You are a commercial real estate intern for B3 Realestate Investment Corporation.
Write a professional, fully-formatted leasing email with the following structure:

- Subject: A compelling subject line about office opportunities at Bayfair Speedway in San Leandro for the business.
- Date: (use the date provided below)
- Greeting: Dear [Contact Name],
- Indent the body paragraphs (use 4 spaces at the start of each new body paragraph).
- Incorporate the following contact and business info in the message when possible:
    - Contact's Email: {contact_email}
    - Contact's Phone Number: {contact_phone}
    - Business Name: {business_name}
    - Industry: {industry}
- Conclude with:
    Best regards,
        Jamie Chen
        {b3_address}
        (123) 456-7890

Only output the email in this format — no explanations, no references to AI, no JSON.

Date: {current_date}
Contact name: {contact_name}

User prompt: {user_prompt}
"""

# --- Ollama & LangChain Setup ---
llm = OllamaLLM(model="llama3")

st.set_page_config(page_title="📬 B3 Leasing Email Generator", layout="centered")
st.title("📬 B3 Leasing Email Generator")
st.markdown("Welcome! Log in and generate professionally formatted leasing emails.")

# --- Login Section ---
st.subheader("👤 Member Login")
first_name = st.text_input("Your First Name")
phone_number = st.text_input("Your Phone Number", type="password")

first_key = first_name.strip().lower()
phone_val = phone_number.strip()
is_member = MEMBERS.get(first_key) == phone_val and first_key in MEMBERS

if not is_member:
    if first_name or phone_number:
        if st.button("Log In"):
            if is_member:
                st.experimental_rerun()
            else:
                st.error("❌ Invalid credentials. Only authorized members may log in.")
    st.stop()

st.success(f"✅ Logged in as: {first_name.capitalize()}")
st.markdown(f"**📧 Your B3 Email Address:** `{B3_ADDRESS}`")
st.markdown("---")

# --- Contact Database Load ---
contacts_db = load_contacts()

# --- Contact Email Lookup ---
st.subheader("📇 Contact Email Lookup")
contact_email = st.text_input("💼 Contact's Email Address")

# Only proceed if email is entered and has '@'
show_followup = False
if contact_email and "@" in contact_email:
    contact_exists = contact_email in contacts_db
    if contact_exists:
        st.success("✅ Contact found in system. (Other details auto-filled.)")
        data = contacts_db[contact_email]
        contact_name = data["name"]
        contact_phone = data["phone"]
        business_name = data["company"]
        industry = data["industry"]
    else:
        st.warning("🔍 New contact, please provide details.")
        contact_name = st.text_input("Contact's Full Name")
        contact_phone = st.text_input("Contact's Phone Number")
        business_name = st.text_input("Contact's Business Name")
        industry = st.text_input("Industry")
        show_followup = True
else:
    st.info("Enter a valid contact email address first.")
    st.stop()

st.subheader("📝 Email Message Prompt")
user_prompt = st.text_area("What would you like the email to say? (Details or special requests)")

if st.button("📨 Generate Leasing Email"):
    missing = []
    if not contact_email: missing.append("Contact Email")
    if not contact_name: missing.append("Contact Name")
    if not contact_phone: missing.append("Contact Phone")
    if not business_name: missing.append("Business Name")
    if not industry: missing.append("Industry")
    if not user_prompt: missing.append("Prompt")
    if missing:
        st.warning("Please complete these fields: " + ", ".join(missing))
    else:
        # Save new contacts if not already in DB
        if not (contact_email in contacts_db):
            contacts_db[contact_email] = {
                "name": contact_name,
                "phone": contact_phone,
                "company": business_name,
                "industry": industry
            }
            save_contacts(contacts_db)
            st.success("📇 New contact saved.")

        username = f"{first_key}_{phone_val}"
        current_date = get_current_email_date()
        history = load_db(username)
        context = get_context(history)

        prompt_filled = prompt_template.format(
            b3_address=B3_ADDRESS,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            business_name=business_name,
            industry=industry,
            current_date=current_date,
            user_prompt=user_prompt
        )
        response = llm.invoke(prompt_filled)
        ai_clean_text = clean_response(response)
        
        st.subheader("✅ Ready-to-Send Email")
        st.text_area("Generated Email", ai_clean_text, height=400)

        # Save conversation
        history.append({"role": "user", "message": user_prompt})
        history.append({"role": "ai", "message": ai_clean_text})
        save_db(username, history)
