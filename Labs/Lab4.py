import os
import sys

# ChromaDB needs a newer sqlite3 than Streamlit Cloud ships with.
__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import streamlit as st
import chromadb
from openai import OpenAI
from pypdf import PdfReader

st.title("📚 Lab 4 — Course Information Chatbot")
st.write(
    "Ask about any of the seven IST course syllabi. Before answering I search a "
    "vector database of those syllabi and pull in the most relevant ones."
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "Lab4-Data")
MODEL = "gpt-5-mini"


def build_vectordb():
    """Read the syllabus PDFs, embed each one, and load them into a Chroma collection."""
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name="Lab4Collection")

    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.lower().endswith(".pdf"):
            continue

        reader = PdfReader(os.path.join(DATA_DIR, filename))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        text = text[:20000]

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )

        collection.add(
            ids=[filename],
            documents=[text],
            embeddings=[response.data[0].embedding],
            metadatas=[{"filename": filename}],
        )

    return collection


# Build it once per session, not on every rerun.
if "Lab4_VectorDB" not in st.session_state:
    with st.spinner("Building the vector database. This runs once."):
        st.session_state.Lab4_VectorDB = build_vectordb()


def search(query, k=3):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )
    return st.session_state.Lab4_VectorDB.query(
        query_embeddings=[response.data[0].embedding],
        n_results=k,
    )


# --- Chatbot ---

if "lab4_messages" not in st.session_state:
    st.session_state.lab4_messages = [
        {"role": "assistant", "content": "Ask me about any of the IST courses."}
    ]

for msg in st.session_state.lab4_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about a course"):
    st.session_state.lab4_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # This is the RAG step. Find the most relevant syllabi, then hand them to the LLM.
    results = search(prompt)
    filenames = results["ids"][0]
    documents = results["documents"][0]

    context = "\n\n".join(
        f"--- {name} ---\n{doc[:6000]}"
        for name, doc in zip(filenames, documents)
    )

    system_prompt = (
        "You are a course information assistant for the Syracuse iSchool.\n\n"
        "Below are the course syllabi most relevant to the question. Answer from them.\n"
        "Begin every reply by naming which syllabus you used, for example "
        "'Using IST 256 Syllabus:'.\n"
        "If the answer is not in the material below, say so plainly and make clear "
        "you are answering from general knowledge instead.\n\n"
        f"RETRIEVED COURSE MATERIAL:\n{context}"
    )

    buffer = st.session_state.lab4_messages[-6:]

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt}] + buffer,
            stream=True,
        )
        response = st.write_stream(stream)

    st.session_state.lab4_messages.append({"role": "assistant", "content": response})