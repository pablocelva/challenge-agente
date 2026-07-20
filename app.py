import streamlit as st
from graph.builder import graph
import uuid

st.set_page_config(
    page_title="BimBam Buy - Asistente IA",
    page_icon="🤖",
    layout="centered"
)

st.title("BimBamIA")
st.title("Asistente de Atencion al Cliente")
st.info("""
Soy el asistente virtual de BimBam Buy. Puedo ayudarte con preguntas sobre:

- Politicas de reembolso y devoluciones
- Programa de afiliados
- Tiempos y costos de envio
- Metodos de pago
- Garantia de productos
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

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


if prompt := st.chat_input("Haz tu pregunta sobre BimBam Buy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Buscando en la documentacion..."):
        response = chat_with_agent(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)