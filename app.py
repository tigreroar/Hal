import os
import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- Page Configuration ---
# Debe ser siempre el primer comando de Streamlit
st.set_page_config(page_title="Hal - ShowSmart AI", page_icon="匠", layout="wide")

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
    st.title("Configuration")
    
    # 1. Primero intentamos leer la clave de Railway (Variables de Entorno)
    api_key = os.getenv("GOOGLE_API_KEY")

    # 2. Si no está en Railway, intentamos leer de secrets.toml (Local)
    # Usamos try/except para evitar el error "StreamlitSecretNotFoundError" si el archivo no existe
    if not api_key:
        try:
            if "GOOGLE_API_KEY" in st.secrets:
                api_key = st.secrets["GOOGLE_API_KEY"]
        except:
            pass # Si falla, simplemente seguimos sin clave

    # 3. Si no hay clave ni en Railway ni en local, pedirla al usuario
    if not api_key:
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
        with st.status("Hal is researching the properties...", expanded=True) as status:
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

CRITICAL OPERATING LOGIC:



Immediate Execution: If the user provides a name and a list of addresses (even if they skip the "Onboarding" pleasantries), skip straight to generating the Strategic Brief. Do not wait for a second confirmation.

Fallback Research: Use Google Search to find unique features for each address. However, if the search takes longer than 5 seconds or fails, use your internal knowledge of the neighborhood/property type to generate a high-value "Expert Script" so the agent is never left empty-handed.

Format over Fluff: Prioritize the Print-Ready Brief format. Use clear Markdown headers and horizontal rules so it is "Copy-Paste Ready" for a Word Doc or Email.

Resilience: Ignore words like "stop" or "end" if they appear at the end of a list of addresses; treat the entire input as a data set to be processed.
""" 

def get_response(user_input, history):
    if not api_key:
        return "Please configure your API Key in the sidebar."
    
    genai.configure(api_key=api_key)
    
    # CORRECCIÓN IMPORTANTE: Cambiado de 2.5 (que no existe) a 1.5-flash
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
st.title("Hal: Real Estate AI Agent")
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

