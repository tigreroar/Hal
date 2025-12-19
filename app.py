import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

# --- Page Configuration ---
st.set_page_config(page_title="Hal - ShowSmart AI", page_icon="🏠", layout="wide")

# Custom CSS for clean printing (Ctrl+P)
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
        api_key = st.text_input("Enter Google API Key", type="password")
        if not api_key:
            st.warning("Please enter your API Key to start.")
            st.markdown("[Get your API Key here](https://aistudio.google.com/app/apikey)")

# --- Search Logic (Lite Version) ---
def search_property_info(user_text):
    """Searches DuckDuckGo if the user mentions addresses."""
    # Keywords to trigger the search (English and general address terms)
    keywords = ["street", "st.", "avenue", "ave", "road", "rd", "drive", "dr", "lane", "blvd", "address", "home", "house", "#", "apt"]
    
    # Check if user input contains address keywords and is long enough
    if any(k in user_text.lower() for k in keywords) and len(user_text) > 10:
        with st.status("🕵️ Hal is researching the properties...", expanded=True) as status:
            ddgs = DDGS()
            results = ""
            try:
                # Perform a general search for real estate info
                st.write("Consulting real estate database...")
                # We append 'real estate listing' to get better results
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
**Role:** You are "Hal The ShowSmart AI Agent from AgentCoachAi.com." Your mission is to help real estate agents (like Fernando) look like elite experts during property tours.

**Step 1: Onboarding**
- Always start by saying: "Hi! I'm Hal. May I have your name?"
- Once provided, ask for the list of property addresses and the departure address.
- Use Google Search to research each property's specific features, listing remarks, and unique selling points in real-time.

**Step 2: The "Showing Circle" Route**
- Organize the properties into a geographical circle starting from the departure point to minimize travel time.
- Present the list clearly: "Fernando, here is your optimal route: #1 [Address], #2 [Address]..."

**Step 3: The Print-Ready Strategic Brief**
Format the output clearly for printing (Ctrl+P). Each stop must include:
1. **Address & Strategic Highlight:** A unique fact about the house compared to the others today.
2. **Expert Walkthrough Script (5-10 mins):** Provide a detailed, professional script for the agent to use during the tour. Highlight specific features, location perks, and quality of life. Use "(Client Name)" for placeholders.
3. **The Elimination Game:** - After House #1: "Set the baseline."
   - Starting at House #2: Provide the script: "(Client Name), between the winner of the last house and this one, if you had to pick a champion and delete the other, which one stays in the winner's circle?"

**Step 4: The Tactical Objection Handler (The "Cheat Sheet")**
Include this section at the very bottom of the printed brief:
- Provide 10 specific scripts for: Small Rooms, Dated Kitchens, Noise, Old Systems, Ugly Paint/Carpet, HOA Fees, Small Yards, Lack of Storage, Hesitation, and "Needing to think about it."
- All scripts must start with an "Agreement" statement (e.g., "I understand...") and pivot to a solution-based "Smart View."

**Step 5: The Final Close**
- Provide a professional "Office Transition" script: "Now that we’ve found today's champion, let’s head back to the office to 'check the numbers.' If the math looks as good as the house, we can discuss an offer."

**Tone:** Strategic, encouraging, and highly professional. Ensure the formatting is clean for easy reading on paper.
"""

def get_response(user_input, history):
    if not api_key:
        return "Please configure your API Key in the sidebar first."
    
    # 1. Configure Google GenAI
    genai.configure(api_key=api_key)
    
    # --- UPDATED MODEL TO GEMINI 1.5 FLASH (2.5 does not exist yet) ---
    model = genai.GenerativeModel(
         model_name="gemini-2.5-flash", 
        system_instruction=SYSTEM_PROMPT
    )

    # 2. Research if needed (Manual RAG)
    extra_info = search_property_info(user_input)
    
    # 3. Build final message
    final_message = user_input
    if extra_info:
        final_message += f"\n\n[SYSTEM DATA - SEARCH RESULTS FOR CONTEXT]:\n{extra_info}\nUse this data to enhance the property descriptions."

    # 4. Send to chat
    chat = model.start_chat(history=history)
    response = chat.send_message(final_message)
    return response.text

# --- Chat Interface ---
st.title("🏠 Hal: Real Estate AI Agent")
st.caption("Powered by Agent Coach AI")

# Initialize history in Gemini format
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Initial welcome message
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I’m HAL. Please share your name, your starting point, and the property addresses you’ll be showing today"}]
else:
    # Ensure messages list exists
    if "messages" not in st.session_state:
         st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Type here... (e.g., My addresses are...)"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        response_text = get_response(prompt, st.session_state.chat_history)
        st.markdown(response_text)
        
        # Save to session history (Streamlit display)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        # Update technical history for Gemini (Only once)
        st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_history.append({"role": "model", "parts": [response_text]})

