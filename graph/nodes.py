from langchain_cohere import ChatCohere
from langchain_core.messages import SystemMessage, HumanMessage
from config import COHERE_API_KEY, LLM_MODEL
from agents.prompts import (
    INTENT_ROUTER_PROMPT, GENERAL_RESPONSE_PROMPT,
    RESPONSE_FORMATTER_PROMPT
)

llm = ChatCohere(
    cohere_api_key=COHERE_API_KEY, 
    model=LLM_MODEL, 
    temperature=0
)

def route_intent(state: dict) -> dict:
    question = state["question"]
    messages = [
        SystemMessage(content=INTENT_ROUTER_PROMPT),
        HumanMessage(content=question)
    ]
    response = llm.invoke(messages)
    intent = response.content.strip().upper()

    if intent not in ["DOCUMENT", "GENERAL"]:
        intent = "DOCUMENT"
    
    return {
        "intent": intent,
        "steps_taken": state.get("steps_taken", []) + ["route_intent"]
    }

def retrieve_documents(state: dict) -> dict:
    from tools.search_tools import search_documents
    question = state["question"]
    context = search_documents.invoke(question)
    return {
        "retrieved_context": context,
        "steps_taken": state.get("steps_taken", []) + ["retrieve_documents"]
    }

def generate_document_response(state: dict) -> dict:
    from agents.document_agent import run_document_agent
    response = run_document_agent(state["question"], state["retrieved_context"])
    return {
        "response": response,
        "messages": [HumanMessage(content=response)],
        "steps_taken": state.get("steps_taken", []) + ["generate_document_response"]
    }

def generate_general_response(state: dict) -> dict:
    question = state["question"]
    messages = [
        SystemMessage(content=GENERAL_RESPONSE_PROMPT),
        HumanMessage(content=question)
    ]
    response = llm.invoke(messages)
    return {
        "response": response.content,
        "messages": [HumanMessage(content=response.content)],
        "steps_taken": state.get("steps_taken", []) + ["generate_general"]
    }

def format_response(state: dict) -> dict:
    question = state["question"]
    context = state["retrieved_context"]
    messages = [
        SystemMessage(content=RESPONSE_FORMATTER_PROMPT.format(
            question=question, information=context
        )),
        HumanMessage(content="Formatea la respuesta final.")
    ]
    response = llm.invoke(messages)
    return {
        "response": response.content,
        "steps_taken": state.get("steps_taken", []) + ["format_response"]
    }