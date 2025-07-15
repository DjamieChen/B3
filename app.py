import json
import os
import streamlit as st
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

DB_DIR = "email_histories"
B3_ADDRESS = "B3investors@gmail.com"

os.makedirs(DB_DIR, exist_ok=True)

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

template = f"""
You are a helpful commercial real estate intern on behalf of B3 Realestate Investment Corporation that sends emails personalized based on the company and the available vacancies we have.

Your email address is {B3_ADDRESS}.

Use the conversation history to answer the user's question, and incorporate the data and information given in this spreadsheet.

Use this as a template but modify it for the specific industry and personalize it for the contact person:

"Hello, I'm __, with B3 Investors, a Bay Area real estate investment and development firm. We are leasing offices to local businesses at our Bayfair Speedway location in San Leandro. We have spaces ranging from 600 to 5000 square feet, suitable for all businesses. This is a great opportunity to move into a more spacious office offered at competitive pricing. The building has its own generator and power grid. Feel free to reach out, and we can provide more information or answer specific questions.

You can contact me at {B3_ADDRESS}."

Conversation history:
{{context}}

User: {{question}}
AI:
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

llm = OllamaLLM(model="llama3")
chain = LLMChain(llm=llm, prompt=prompt)

# --- Streamlit UI ---
st.title("B3 Real Estate Email AI Chatbot")
st.write("Send and track personalized real estate emails. Your address: **B3investors@gmail.com**")

username = st.text_input("Enter your email/username:", key="username")
if username:
    history = load_db(username)
    st.subheader("Conversation History")
    if history:
        for entry in history:
            st.markdown(f"**{entry['role'].capitalize()}:** {entry['message']}")
    else:
        st.info("No previous conversation found. Start a new one below!")

    user_input = st.text_input("Type your message:", key="user_input")
    if st.button("Send") and user_input:
        context = get_context(history)
        with st.spinner("Generating reply..."):
            response = chain.invoke({"context": context, "question": user_input})
        st.markdown(f"**AI:** {response}")

        # Update and save history
        history.append({"role": "user", "message": user_input})
        history.append({"role": "ai", "message": response})
        save_db(username, history)
        st.experimental_rerun()  # Refresh to show updated history

    if st.button("Clear Conversation"):
        save_db(username, [])
        st.experimental_rerun()
else:
    st.info("Please enter the desired email to begin process.")

