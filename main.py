import json
import os
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Configuration
DB_DIR = "email_histories"
B3_ADDRESS = "B3investors@gmail.com"

# Ensure history folder exists
os.makedirs(DB_DIR, exist_ok=True)

# File helper functions
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

# Prompt template
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

# LangChain setup
prompt = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

llm = OllamaLLM(model="llama3")
chain = LLMChain(llm=llm, prompt=prompt)

# Clean the AI's response
def clean_response(text):
    # Remove triple quotes if present
    text = text.strip().strip('"').strip("'")
    # Replace escaped newlines and quotes
    text = text.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
    return text.strip()

# Main CLI app
def main():
    print("📬 Welcome to the B3 Email AI chatbot!")
    print("Type 'exit' to quit.")
    username = input("Enter your email/username: ").strip().lower()
    history = load_db(username)

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        context = get_context(history)
        response = chain.invoke({"context": context, "question": user_input})
        ai_raw = response.get("text", "")
        ai_reply = clean_response(ai_raw)

        print("\n📧 AI-Generated Email:\n")
        print(ai_reply + "\n")

        history.append({"role": "user", "message": user_input})
        history.append({"role": "ai", "message": ai_reply})
        save_db(username, history)

if __name__ == "__main__":
    main()
