import streamlit as st
import time
import speech_recognition as sr
import pyttsx3
from pypdf import PdfReader
from groq import Groq

st.set_page_config(page_title="B.Tech Study Companion", page_icon="🎓")
st.title("🎓 B.Tech 3rd Sem Study Companion")

# ==========================================
# 1. SIDEBAR SETUP (API Key, PDF, Settings)
# ==========================================
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Groq API Key", type="password")
    uploaded_pdf = st.file_uploader("Upload Lecture Notes (PDF)", type=["pdf"])
    enable_voice_out = st.checkbox("Read answers aloud (TTS)", value=False)
    
    st.divider()
    st.header("Quick Actions")
    quiz_btn = st.button("📝 Quiz / Viva Me", use_container_width=True)
    summary_btn = st.button("📄 Summarize Notes", use_container_width=True)
    timer_btn = st.button("⏱️ Start Focus Timer", use_container_width=True)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def speak(text):
    """Speaks text aloud using pyttsx3 safely inside Streamlit."""
    clean_text = text.replace("*", "").replace("#", "")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
        engine.setProperty('rate', 175)
        engine.say(clean_text)
        engine.runAndWait()
    except Exception as e:
        st.warning(f"Audio playback skipped: {e}")

@st.cache_data
def read_pdf(file):
    """Extracts up to 15 pages from the uploaded PDF."""
    reader = PdfReader(file)
    text = ""
    for page in reader.pages[:15]:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text[:15000]

def listen_mic():
    """Listens to the microphone and converts speech to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        with st.spinner("Listening... Speak now!"):
            recognizer.pause_threshold = 1
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=6)
                return recognizer.recognize_google(audio, language='en-in')
            except Exception:
                st.error("Couldn't catch that. Please try again.")
                return None

# ==========================================
# 3. INITIALIZE MEMORY & SYSTEM PROMPT
# ==========================================
pdf_text = read_pdf(uploaded_pdf) if uploaded_pdf else ""

system_prompt = (
    "You are an expert B.Tech 3rd Semester AI & Engineering Tutor. "
    "Your core subjects are Data Structures & Algorithms, Object-Oriented Programming, "
    "Discrete Mathematics, and Digital Logic. "
    "Keep answers concise (3 to 4 sentences max) unless asked for a 5-mark exam answer. "
    "Never use markdown formatting like asterisks or hashtags."
)
if pdf_text:
    system_prompt += f"\n\nPrioritize answering using these uploaded lecture notes:\n{pdf_text}"

# Store chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Your B.Tech Study Companion is ready. Ask a question or use the sidebar buttons!"}
    ]

# ==========================================
# 4. HANDLE FOCUS TIMER BUTTON
# ==========================================
if timer_btn:
    with st.status("Focus timer running... Put your phone away!", expanded=True):
        time.sleep(5)  # 5-second demo timer
        st.write("Focus session complete! Great work.")
    if enable_voice_out:
        speak("Focus session complete! Great work.")

# ==========================================
# 5. DISPLAY CHAT HISTORY
# ==========================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ==========================================
# 6. CAPTURE USER INPUT (Text, Mic, or Buttons)
# ==========================================
col1, col2 = st.columns([6, 1])
with col1:
    text_query = st.chat_input("Ask a question about DSA, OOP, Discrete Math...")
with col2:
    mic_btn = st.button("🎤", help="Speak your question")

user_prompt = None

if quiz_btn:
    user_prompt = "Ask me ONE short viva question based on my uploaded notes or B.Tech 3rd sem syllabus. Wait for my reply before telling me the answer."
elif summary_btn:
    user_prompt = "Give me a crisp 4-sentence summary of the key topics in my notes or syllabus."
elif mic_btn:
    user_prompt = listen_mic()
elif text_query:
    user_prompt = text_query

# ==========================================
# 7. GET AI RESPONSE FROM GROQ
# ==========================================
if user_prompt:
    if not api_key:
        st.warning("Please enter your Groq API Key in the left sidebar first.")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # Call Groq API
    client = Groq(api_key=api_key)
    api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=api_messages,
                    temperature=0.5,
                    max_tokens=300,
                )
                reply = completion.choices[0].message.content
            except Exception as e:
                reply = f"API Error: {e}"
            
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            if enable_voice_out:
                speak(reply)
