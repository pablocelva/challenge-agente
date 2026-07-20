from typing import TypedDict, Annotated, List
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    intent: str
    retrieved_context: str
    response: str
    steps_taken: List[str]