from langchain_core.tools import tool

@tool
def search_documents(query: str):
    """Busca informacion en la documentacion oficial de BimBam Buy."""
    from rag.vectorstore import load_vectorstore, get_retriever
    vectorstore = load_vectorstore()
    retriever = get_retriever(vectorstore, k=4)
    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context