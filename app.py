import streamlit as st
import requests
import os

st.set_page_config(page_title="Policy AMA Chat", layout="centered")
st.title("Policy AMA 📝")

# --- Sticky Input Box & Chat Message CSS ---
st.markdown(
    """
    <style>
    .user-message {
        background-color: #494c4d;
        color: white;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
    }
    .assistant-message {
        background-color: #4d4dab;
        color: white;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
    }
    .stForm {
        position: sticky;
        bottom: 0;
        background-color: #494c4d;
        padding-top: 10px;
        border-top: 1px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "processing_logs" not in st.session_state:
    st.session_state.processing_logs = []
if "waiting_for_response" not in st.session_state:
    st.session_state.waiting_for_response = False

# --- API Setup ---
api_key = os.getenv("PERPLEXITY_API_KEY")
if not api_key:
    st.error("❌ PERPLEXITY_API_KEY environment variable is missing.")
    st.stop()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

allowed_models = [
    "pplx-7b-online",
    "sonar-pro",
    "sonar-reasoning-pro",
    "llama2-70b-chat",
    "gpt-3.5-turbo-1106",
]

# --- Safe Rerun ---
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# --- Function to get response ---
def get_response(user_input, history):
    messages = [{
        "role": "system",
        "content": (
            "You are an insurance policy explainer for customers without legal or technical background.\n"
            "Please answer clearly, using:\n"
            "- Short sentences\n"
            "- Bullet points where possible\n"
            "- Tables for inclusions/exclusions\n"
            "- **Bold** key terms and numbers\n"
            "- Avoid legal jargon and filler\n"
        )
    }]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})

    st.session_state.processing_logs.clear()
    result_content = None
    last_error = None

    for model in allowed_models:
        st.session_state.processing_logs.append(f"🔄 Trying model: {model}")
        try:
            resp = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages, "max_tokens": 350},
                timeout=15,
            )
            st.session_state.processing_logs.append(f"Response status code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                result_content = data["choices"][0]["message"]["content"]
                st.session_state.processing_logs.append("✅ Successfully received response.")
                break
            elif "invalid_model" in resp.text.lower():
                st.session_state.processing_logs.append(f"⚠️ Model {model} not valid, trying next model...")
                continue
            else:
                last_error = f"Error {resp.status_code}: {resp.text}"
                st.session_state.processing_logs.append(last_error)
                break
        except requests.Timeout:
            last_error = "Error: Request timed out after 15 seconds."
            st.session_state.processing_logs.append(last_error)
            break
        except Exception as e:
            last_error = f"Exception: {str(e)}"
            st.session_state.processing_logs.append(last_error)
            break

    if result_content:
        return result_content
    else:
        return f"❌ No model succeeded. Last error: {last_error or 'Unknown error.'}"

# --- Conversation UI ---
st.subheader("💬 Conversation")
if st.session_state.chat_history:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-message'>**You:**<br>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-message'>**Policy AMA:**<br>{msg['content']}</div>", unsafe_allow_html=True)
else:
    st.info("No conversation yet. Enter a clause or question below to begin.")

# --- Show Processing Logs ---
if st.session_state.processing_logs:
    with st.expander("🔎 Processing Details (click to expand)", expanded=True):
        for log in st.session_state.processing_logs:
            st.write(log)

# --- Input Form ---
st.markdown("---")
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area("Type a policy clause or follow-up question:", height=100)
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        send = st.form_submit_button("Send")
    with col2:
        clear = st.form_submit_button("Clear Conversation")

# --- Handle Actions ---
if send and user_input.strip():
    st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
    st.session_state.chat_history.append({"role": "assistant", "content": "💭 Thinking..."})
    st.session_state.waiting_for_response = True
    safe_rerun()

if clear:
    st.session_state.chat_history.clear()
    st.session_state.processing_logs.clear()
    st.session_state.waiting_for_response = False
    safe_rerun()

# --- Process Waiting State ---
if st.session_state.waiting_for_response:
    user_message = st.session_state.chat_history[-2]["content"]
    response = get_response(user_message, st.session_state.chat_history[:-2])
    st.session_state.chat_history[-1] = {"role": "assistant", "content": response}
    st.session_state.waiting_for_response = False
    safe_rerun()
