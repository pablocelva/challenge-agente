def decide_next_step(state: dict) -> str:
    intent = state.get("intent", "DOCUMENT")
    if intent == "DOCUMENT":
        return "retrieve_documents"
    else:
        return "generate_general_response"

def should_format(state: dict) -> str:
    intent = state.get("intent", "DOCUMENT")
    if intent == "DOCUMENT":
        return "format_response"
    return "end"