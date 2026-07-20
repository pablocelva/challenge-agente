import streamlit as st
from graph.builder import graph
import uuid

st.set_page_config(
    page_title="BimBam Buy - Asistente IA",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(45deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    .block-container {
        padding-top: 2rem !important;
    }
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1.1rem;
    }
    [data-testid="stChatInput"] {
        background: white;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>💬 BimBamIA</h1>
    <p>Asistente Virtual de Atención al Cliente</p>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

preguntas_sugeridas = [
    "¿Cuál es el plazo para devolver un producto?",
    "¿Cómo funciona el programa de afiliados?",
    "¿Cuánto cuesta el envío y cuánto tarda?",
    "¿Qué métodos de pago aceptan?",
    "¿Cómo reclamo la garantía de un producto?",
    "¿Puedo cambiar un producto sin abrirlo?",
    "¿Cuánto tarda en llegar mi reembolso?",
    "¿Cómo me afilio a BimBam Buy?",
]

if not st.session_state.messages:
    st.markdown("### 💡 Preguntas sugeridas")
    st.markdown("Copia y pega cualquiera de estas en el chat:")
    cols = st.columns(2)
    for i, pregunta in enumerate(preguntas_sugeridas):
        col = cols[i % 2]
        col.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.25);
            color: white;
            padding: 0.6rem 1rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        ">{pregunta}</div>
        """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def chat_with_agent(message: str) -> str:
    thread_id = str(uuid.uuid4())
    thread_config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [],
        "question": message,
        "intent": "",
        "retrieved_context": "",
        "response": "",
        "steps_taken": []
    }

    result = graph.invoke(initial_state, thread_config)
    return result["response"]


if prompt := st.chat_input("Escribí tu pregunta sobre BimBam Buy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("🔍 Buscando en la documentación..."):
        response = chat_with_agent(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

# if st.session_state.messages:
#     if st.button("🗑️ Limpiar chat", use_container_width=True):
#         st.session_state.messages = []
#         st.rerun()