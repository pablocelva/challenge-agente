from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from graph.state import AgentState
from graph.nodes import (
    route_intent, retrieve_documents,
    generate_document_response, generate_general_response, format_response
)
from graph.edges import decide_next_step, should_format
import sqlite3

def build_graph():
    conn = sqlite3.connect("checkpoint.db", check_same_thread=False)
    memory = SqliteSaver(conn)

    builder = StateGraph(AgentState)

    builder.add_node("route_intent", route_intent)
    builder.add_node("retrieve_documents", retrieve_documents)
    builder.add_node("generate_document_response", generate_document_response)
    builder.add_node("generate_general_response", generate_general_response)
    builder.add_node("format_response", format_response)

    builder.set_entry_point("route_intent")

    builder.add_conditional_edges(
        "route_intent",
        decide_next_step,
        {
            "retrieve_documents": "retrieve_documents",
            "generate_general_response": "generate_general_response",
        }
    )

    builder.add_edge("retrieve_documents", "generate_document_response")
    builder.add_conditional_edges(
        "generate_document_response",
        should_format,
        {
            "format_response": "format_response",
            "end": END
        }
    )

    builder.add_edge("generate_general_response", END)
    builder.add_edge("format_response", END)

    graph = builder.compile(checkpointer=memory)
    return graph

graph = build_graph()