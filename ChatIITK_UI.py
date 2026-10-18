import gc
import os
import re
from html import escape
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="ChatIITK",
    page_icon=":material/school:",
    initial_sidebar_state="expanded",
)

import torch
from langchain_classic.chains import RetrievalQA

from constants import MODELS
from load_models import build_llm
from prompt_template_utils import get_prompt_template
from reranker import RerankedRetriever, load_reranker
from utils import open_vector_store

TOP_K = 6
FETCH_K = 30

SUGGESTIONS = [
    "Where does IIT Kanpur rank among Indian institutes?",
    "Which clubs and societies are there on campus?",
    "How do semester credits and grading work?",
]

REWRITE_SYSTEM = (
    "Rewrite the student's last question so it makes sense on its own, without the conversation. "
    "Replace words like 'those', 'it', 'that', 'them' with what they refer to. "
    "Refer to groups by name (for example 'the gymkhana clubs') and do not list their individual members. "
    "Never expand, translate or guess the meaning of abbreviations (STC, CMHW, DoAA, DoRA, SnT and so on): copy them exactly as written. "
    "If the question already makes sense on its own, output it unchanged. "
    "Do not answer the question. Output only the rewritten question on one line, "
    "with no introduction and no explanation."
)

REFERENCE = re.compile(r"\b(it|its|that|this|those|these|them|they|their|he|she|his|her|there|former|latter|same|one)\b", re.IGNORECASE)
FOLLOW_UP = re.compile(r"^\s*(and|also|then|so|but|what about|how about|what if)\b", re.IGNORECASE)
ACRONYM = re.compile(r"\b[A-Za-z]*[A-Z][A-Za-z]*[A-Z][A-Za-z]*\b")

LABEL = re.compile(r"^(the )?(rewritten|standalone) question\s*:\s*", re.IGNORECASE)
PREAMBLE = re.compile(r"^(here is|here's|here are|sure|certainly|of course|okay)\b", re.IGNORECASE)


def rewrite_prompt(model_type, history, question):
    body = f"Conversation:\n{history}\n\nLast question: {question}"
    if model_type == "llama3":
        return (
            "<|start_header_id|>system<|end_header_id|>\n\n" + REWRITE_SYSTEM + "<|eot_id|>"
            + "<|start_header_id|>user<|end_header_id|>\n\n" + body + "<|eot_id|>"
            + "<|start_header_id|>assistant<|end_header_id|>\n\n"
        )
    if model_type == "llama":
        return "[INST] <<SYS>>\n" + REWRITE_SYSTEM + "\n<</SYS>>\n\n" + body + " [/INST]"
    return "[INST] " + REWRITE_SYSTEM + "\n\n" + body + " [/INST]"


@st.cache_resource(show_spinner="Opening the index...")
def load_store():
    return open_vector_store()


@st.cache_resource(max_entries=1, show_spinner=False)
def load_llm(model_id):
    return build_llm(model_id)


def release_llm():
    st.session_state.pop("qa", None)
    load_llm.clear()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


@st.cache_resource(show_spinner="Loading the passage re-ranker...")
def load_reranker_model():
    return load_reranker()


def new_chain(llm, store, model_type):
    prompt, memory = get_prompt_template(promptTemplate_type=model_type, history=True)
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=RerankedRetriever(
            store=store, reranker=load_reranker_model(), fetch_k=FETCH_K, top_k=TOP_K
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt, "memory": memory},
    )


def clean_rewrite(raw):
    for line in raw.strip().splitlines():
        line = line.strip().strip('"').strip()
        line = LABEL.sub("", line).strip().strip('"').strip()
        if not line or line.endswith(":") or PREAMBLE.match(line):
            continue
        return line
    return None


def standalone_question(llm, model_type, question, messages):
    if not messages:
        return question
    if not (REFERENCE.search(question) or FOLLOW_UP.search(question)):
        return question
    lines = []
    for m in messages[-4:]:
        who = "Student" if m["role"] == "user" else "ChatIITK"
        lines.append(f"{who}: {m['content'][:1500]}")
    prompt = rewrite_prompt(model_type, "\n".join(lines), question)
    try:
        rewritten = clean_rewrite(llm.invoke(prompt))
    except Exception:
        return question
    if not rewritten or len(rewritten) > 300:
        return question
    if any(word.lower() not in rewritten.lower() for word in ACRONYM.findall(question)):
        return question
    return rewritten


def describe(doc):
    name = os.path.basename(doc.metadata["source"])
    page = doc.metadata.get("page")
    return f"{name}, page {page + 1}" if isinstance(page, int) else name


def apply_style():
    css = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def section(title, count=None):
    extra = f"<span>{count}</span>" if count is not None else ""
    st.markdown(
        f'<div class="section-label">{escape(title)}{extra}</div>',
        unsafe_allow_html=True,
    )


def role_label(role):
    name, css = ("You", "role-user") if role == "user" else ("ChatIITK", "role-assistant")
    st.markdown(f'<div class="role {css}">{name}</div>', unsafe_allow_html=True)


def show_sources(sources):
    if not sources:
        return
    section("Sources", len(sources))
    for label, text in sources:
        with st.expander(label):
            st.code(text, language=None, wrap_lines=True)


def show_notes(model, searched):
    rows = []
    if model:
        rows.append(f'<div class="meta"><b>Model</b>{escape(model)}</div>')
    if searched:
        rows.append(f'<div class="meta"><b>Searched for</b>{escape(searched)}</div>')
    if rows:
        st.markdown("".join(rows), unsafe_allow_html=True)


def ask(text):
    st.session_state.pending = text


apply_style()
store = load_store()

with st.sidebar:
    st.markdown(
        '<div class="side-brand">ChatIITK</div>'
        '<div class="side-tag">Lluminating Language</div>',
        unsafe_allow_html=True,
    )
    section("Answering")
    use_model = st.toggle(
        "Answer with a language model",
        value=True,
        help="Off: skip the model and show only the closest chunks from the database.",
    )
    model_name = st.selectbox(
        "Model",
        list(MODELS),
        disabled=not use_model,
        help="Switching clears the conversation and loads the new model, "
        "downloading it first if it is not on this computer yet.",
    )
    section("Index")
    st.markdown(
        f'<div class="stat"><span>{store._collection.count():,}</span>passages indexed</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Clear conversation", key="clear"):
        st.session_state.messages = []
        st.session_state.pop("qa", None)
        st.rerun()

model_id, model_type = MODELS[model_name]
if st.session_state.get("active_model") not in (None, model_name):
    release_llm()
    st.session_state.messages = []
st.session_state.active_model = model_name

st.markdown(
    '<div class="masthead">'
    '<div class="eyebrow">Lluminating Language &middot; IIT Kanpur</div>'
    '<div class="title">ChatIITK</div>'
    '<p class="lede">Ask about the institute. Answers are drawn only from the indexed '
    "documents, and the passages behind each answer are listed beneath it.</p>"
    "</div>",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

question = st.chat_input("Ask something about IIT Kanpur") or st.session_state.pop("pending", None)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        role_label(message["role"])
        st.write(message["content"])
        show_notes(message.get("model"), message.get("searched"))
        show_sources(message.get("sources", []))

suggestions = st.empty()
if not st.session_state.messages and not question:
    with suggestions.container():
        section("Try asking")
        for i, text in enumerate(SUGGESTIONS):
            st.button(text, key=f"prompt_{i}", on_click=ask, args=(text,))

if question:
    with st.chat_message("user"):
        role_label("user")
        st.write(question)

    with st.chat_message("assistant"):
        role_label("assistant")
        searched = None
        used_model = None
        try:
            if use_model:
                used_model = model_name
                with st.spinner(
                    f"Working with {model_name}. The first answer after choosing a model "
                    "loads it, which can take a while."
                ):
                    llm = load_llm(model_id)
                    if "qa" not in st.session_state:
                        st.session_state.qa = new_chain(llm, store, model_type)
                    search_text = standalone_question(
                        llm, model_type, question, st.session_state.messages
                    )
                    if search_text != question:
                        searched = search_text
                    result = st.session_state.qa.invoke({"query": search_text})
                reply = result["result"].strip()
                sources = [(describe(d), d.page_content) for d in result["source_documents"]]
            else:
                found = store.similarity_search_with_score(question, k=TOP_K)
                reply = "The closest passages in the index:"
                sources = [
                    (f"{describe(d)} (distance {score:.3f})", d.page_content)
                    for d, score in found
                ]
        except Exception as error:
            st.error(f"That did not work: {error}")
            st.stop()
        st.write(reply)
        show_notes(used_model, searched)
        show_sources(sources)

    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
            "sources": sources,
            "searched": searched,
            "model": used_model,
        }
    )
