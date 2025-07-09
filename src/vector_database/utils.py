# utils.py

import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR = os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from typing import Dict
import time
import logging
from src.validators.pinecone_validators import IndexNameStructure, ExpectedNewData

logger = logging.getLogger(__name__)

class PineconeManagment:

    def __init__(self):
        logger.info("Setting pinecone connection...")

    def reading_datasource(self):
        # 1) Point at your PDF
        pdf_path = os.path.join(WORKDIR, "faq", "Current Essentials of Medicine.pdf")
        loader = PyPDFLoader(pdf_path)

        # 2) Split into ~1,000-character chunks with 200-character overlap
        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        pages = loader.load_and_split(text_splitter=splitter)

        # 3) Wrap each chunk in a Document, with metadata for tracing
        docs = []
        for i, page in enumerate(pages, start=1):
            docs.append(
                Document(
                    page_content=page.page_content,
                    metadata={"source": "Current Essentials of Medicine.pdf", "chunk": i}
                )
            )
        return docs

    # … rest of your methods unchanged …
    
    def creating_index(
        self,
        index_name: str,
        docs: list[Document],
        dimension: int = 3072,
        metric: str = "cosine",
        embedding = OpenAIEmbeddings(model="text-embedding-3-large"),
    ):
        logger.info(f"Creating index {index_name}...")
        IndexNameStructure(index_name=index_name)

        # 1) Create the Pinecone index
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        existing = [info["name"] for info in pc.list_indexes()]
        if index_name in existing:
            raise Exception(f"The index '{index_name}' already exists.")
        pc.create_index(
            name=index_name.lower(),
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)
        logger.info(f"Index '{index_name}' is ready.")

        # 2) Batch‐upload your documents
        store = PineconeVectorStore(index_name=index_name, embedding=embedding)
        batch_size = 50  # adjust smaller if you still hit size limits
        total_docs = len(docs)
        batches = (total_docs + batch_size - 1) // batch_size

        for batch_num in range(batches):
            start = batch_num * batch_size
            end = min(start + batch_size, total_docs)
            batch_docs = docs[start:end]
            store.add_documents(batch_docs)
            logger.info(f"  • Uploaded docs {start}–{end-1}")

        logger.info(f"Finished uploading {total_docs} docs in {batches} batches.")

        
    def loading_vdb(self, index_name: str, embedding=OpenAIEmbeddings(model="text-embedding-3-large")):
        logger.info("Loading vector database from Pinecone...")
        self.vdb =  PineconeVectorStore(index_name=index_name, embedding=embedding)
        logger.info("Vector database loaded...")
    

    def adding_documents(self, new_info: Dict[str,str]):
        ExpectedNewData(new_info = new_info)
        logger.info("Adding data in the vector database...")
        self.vdb.add_documents([Document(page_content="question: " + new_info['question'] + '\n answer: ' + new_info['answer'], metadata={"question": new_info['question']})])
        logger.info("More info added in the vector database...")
    


    def finding_similar_docs(self, user_query):
        docs = self.vdb.similarity_search_with_relevance_scores(
                    query = user_query,
                    k = 3,
                    score_threshold=0.9
                )
        
        return docs
    
    
    