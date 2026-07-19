from langchain_cohere import CohereEmbeddings
from config import EMBEDDING_MODEL

def get_embeddings():
    return CohereEmbeddings(
        model=EMBEDDING_MODEL
    )