import streamlit as st
from openai import OpenAI

st.title("💬 Lab 3 — Streaming Chatbot")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SYSTEM_PROMPT = """You are a friendly assistant talking to a 10 year old.
Explain everything in simple words and short sentences. Use everyday examples.

Follow this pattern every time:
1. Answer the question.
2. Then ask exactly: "Do you want more info?"

If the user says yes, give more detail on the same topic, then ask "Do you want more info?" again.
If the user says no, say something friendly and ask what else you can help with.
Never skip the question."""


def build_buffer(messages, max_user_turns=2):
    """Keep only the last two user messages and the replies that follow them."""
    user_spots = [i for i, m in enumerate(messages) if m["role"] == "user"]
    if len(user_spots) <= max_user_turns:
        return messages
    start = user_spots[-max_user_turns]
    return messages[start:]


# Conversation memory lives here.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! What would you like to know?"}
    ]

# Show everything said so far.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    buffer = build_buffer(st.session_state.messages)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + buffer,
            stream=True,
        )
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})