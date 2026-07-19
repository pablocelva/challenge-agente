from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from config import COHERE_API_KEY, LLM_MODEL

MULTI_QUERY_PROMPT = """
Eres un asistente de busqueda. Genera cinco versiones diferentes de la
pregunta del usuario para recuperar documentos relevantes de una
base de datos vectorial. Genera unicamente las preguntas alternativas
separadas en lineas diferentes, sin texto adicional.

PREGUNTA ORIGINAL: {question}

FORMATO DE SALIDA:
["primera pregunta","segunda pregunta",...,"quinta pregunta"]
"""

def get_multi_query_chain():
    llm = ChatCohere(
        cohere_api_key=COHERE_API_KEY,
        model=LLM_MODEL,
        temperature=0.5
    )
    prompt = ChatPromptTemplate.from_template(MULTI_QUERY_PROMPT)
    chain = prompt | llm | CommaSeparatedListOutputParser()
    return chain

def generate_query_variants(question: str) -> list:
    chain = get_multi_query_chain()
    variants = chain.invoke({"question": question})
    return variants

def multi_query_retrieval(question: str, retriever) -> str:
    variants = generate_query_variants(question)
    all_docs = []
    for variant in variants:
        docs = retriever.invoke(variant)
        all_docs.extend(docs)
    
    seen = set()
    unique_docs = []
    for doc in all_docs:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            unique_docs.append(doc)
    
    context = "\n".join([doc.page_content for doc in unique_docs[:6]])
    return context