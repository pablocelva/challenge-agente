from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def load_pdfs(docs_dir: str = "docs") -> list:
    documents = []
    for filename in os.listdir(docs_dir):
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(docs_dir, filename))
            documents.extend(loader.load())
    return documents

def split_documents(documents: list, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    return splitter.split_documents(documents)