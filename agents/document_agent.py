from langchain_cohere import ChatCohere
from langchain_core.messages import SystemMessage, HumanMessage
from config import COHERE_API_KEY, LLM_MODEL
from agents.prompts import DOCUMENT_AGENT_PROMPT

llm = ChatCohere(
    cohere_api_key=COHERE_API_KEY,
    model=LLM_MODEL,
    temperature=0
)

def run_document_agent(question: str, context: str) -> str:
    messages = [
        SystemMessage(context=DOCUMENT_AGENT_PROMPT.format(context=context)),
        HumanMessage(content=question)
    ]
    response = llm.invoke(messages)
    return response.content