import streamlit as st
from openai import OpenAI, AuthenticationError
from pypdf import PdfReader

st.title("📄 Lab 2 — Document Summarizer")
st.write("Upload a PDF and choose how you'd like it summarized.")

# Get the API key from Streamlit secrets instead of asking the user.
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_api_key)

try:
    client.models.list()
except AuthenticationError:
    st.error("The API key in secrets is invalid.", icon="🚫")
    st.stop()

# --- Sidebar options ---

language = st.sidebar.selectbox(
    "Summary language",
    ["English", "Spanish", "French", "German", "Chinese"],
)

summary_type = st.sidebar.selectbox(
    "Type of summary",
    [
        "Summarize the document in 100 words",
        "Summarize the document in 2 connecting paragraphs",
        "Summarize the document in 5 bullet points",
    ],
)

use_advanced = st.sidebar.checkbox("Use advanced model")
model = "gpt-5-mini" if use_advanced else "gpt-5-nano"
st.sidebar.write(f"Model in use: `{model}`")

# --- Summarize ---

uploaded_file = st.file_uploader("Upload a PDF", type=("pdf",))

if uploaded_file:
    reader = PdfReader(uploaded_file)
    document = "\n\n".join(page.extract_text() or "" for page in reader.pages)

    messages = [
        {
            "role": "user",
            "content": f"Here's a document:\n\n{document}\n\n---\n\n"
                       f"{summary_type}. Write the summary in {language}.",
        }
    ]

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
    st.write_stream(stream)