from langchain_openai import ChatOpenAI
from typing import Literal

def format_retrieved_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_model(provider:Literal['openai']):
    if provider == "openai":
        return ChatOpenAI(temperature=0, model_name="gpt-4o-mini")    