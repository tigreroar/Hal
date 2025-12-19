import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- Page Configuration ---
st.set_page_config(page_title="Hal - ShowSmart AI", page_icon="🏠", layout="wide")

# Custom CSS for clean printing
st.markdown("""
    <style>
        @media print {
            [data-testid="stSidebar"] {display: none;}
            .stChatInput {display: none;}
            .stMarkdown {font-size: 12pt;}
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar: Configuration ---
with st.sidebar:
    st.title("🔧 Configuration")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter your Google API Key", type="password")
        if not api_key:
            st.warning("Please enter your API Key to start.")
            st.markdown("[Get your API Key here](https://aistudio.google.com/app/apikey)")

# --- Search Logic (Lite Version) ---
def search_property_info(user_text):
    # Keywords to identify if the user is talking about addresses
    keywords = ["avenue", "road", "st", "street", "dr", "drive", "lane", "blvd", "home", "house", "address", "#"]
    
    # Check if keywords exist and text is long enough
    if any(k in user_text.lower() for k in keywords) and len(user_text) > 10:
        with st.status("🕵️ Hal is researching the properties...", expanded=True) as status:
            ddgs = DDGS()
            results = ""
            try:
                st.write("Consulting real estate database...")
                search_results = ddgs.text(user_text + " real estate listing features", max_results=4)
                
                if search_results:
                    for r in search_results:
                        results += f"- {r['title']}: {r['body']}\n"
                
                status.update(label="Research complete!", state="complete", expanded=False)
                return results
            except Exception as e:
                status.update(label="Search error (continuing without external data)", state="error")
                return ""
    return ""

# --- Gemini Model Configuration ---
SYSTEM_PROMPT = """
Role: You are "Hal The ShowSmart AI Agent from AgentCoachAi.com." Your mission is to help real estate agents like Fernando look like elite experts during property tours.

Step 1: Onboarding
- Always start by saying: "Hi! I'm Hal. May I have your name?"
- Once provided, ask for the list of property addresses and the departure address.
- Use Google Search to research each property's specific features.

Step 2: The "Showing Circle" Route
- Organize the properties into a geographical circle starting from the departure point.
- Present the list clearly: "Fernando, here is your optimal route: #1 [Address], #2 [Address]..."

Step 3: The Print-Ready Strategic Brief
Format the output clearly for printing. Each stop must include:
1. Address & Strategic Highlight: A unique fact about the house.
2. Expert Walkthrough Script (5-10 mins): A professional script for the agent.
3. The Elimination Game: After House #1, ask which house stays in the winner's circle.

Step 4: The Tactical Objection Handler
Include specific scripts for: Small Rooms, Dated Kitchens, Noise, etc.
All scripts must start with an "Agreement" statement and pivot to a "Smart View."

Step 5: The Final Close
- Provide a professional "Office Transition" script to head back to the office.

Tone: Strategic, encouraging, and highly professional.
""" 

def get_response(user_input, history):
    if not api_key:
        return "Please configure your API Key in the sidebar."
    
    genai.configure(api_key=api_key)
    
    # Using gemini-1.5-flash (Fixed from 2.5 which does not exist yet)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=SYSTEM_PROMPT
    )

    # Manual Search (RAG)
    extra_info = search_property_info(user_input)
    
    final_message = user_input
    if extra_info:
        final_message += f"\n\n[SYSTEM DATA - SEARCH RESULTS]:\n{extra_info}\nUse this data to enhance descriptions."

    chat = model.start_chat(history=history)
    response = chat.send_message(final_message)
    return response.text

# --- Chat Interface ---
st.title("🏠 Hal: Real Estate AI Agent")
st.caption("Powered by Agent Coach AI")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm HAL. Please share your name, starting point, and the property addresses."}]

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Type here... (e.g., My addresses are...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = get_response(prompt, st.session_state.chat_history)
        st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        # Update technical history for Gemini
        st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_history.append({"role": "model", "parts": [response_text]})
