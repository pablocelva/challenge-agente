from langchain_chroma import Chroma
from rag.embeddings import get_embeddings
from rag.loader import load_pdfs, split_documents

PERSIST_DIR = "chroma_db"

def create_vectorstore(docs_dir: str = "docs") -> Chroma:
    docs = load_pdfs(docs_dir)
    chunks = split_documents(docs)
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )
    return vectorstore

def load_vectorstore() -> Chroma:
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

def get_retriever(vectorstore: Chroma, k: int = 4):
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )