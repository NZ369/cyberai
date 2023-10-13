import os
import openai, langchain, pinecone
from langchain.agents import Tool
from pydantic import BaseModel, Field
from llms.azure_llms import create_azure_embedder, create_llm
from langchain.document_loaders import DirectoryLoader, UnstructuredPDFLoader, OnlinePDFLoader, PyPDFLoader
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from langchain.tools import BaseTool, Tool
from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

#load environment variables
load_dotenv()

PINECONE_API_KEY= os.getenv("PINECONE_API_KEY")
PINECONE_ENV = "us-west4-gcp-free"

pinecone.init(
    api_key = PINECONE_API_KEY,
    environment = PINECONE_ENV
)

index_name = 'cyberai'

embeddings = create_azure_embedder()
vectorstore = Pinecone.from_existing_index(index_name, embeddings, "text")
llm = create_llm(max_tokens=2000, temp=0)

class knowledgebase_tool(BaseTool):
    name = "Cybersecurity Knowledgebase"
    description = "Searches and returns information regarding cybersecurity practices and procedures"
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever(search_kwargs={'k': 3}))
        return qa.run(query)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
main_retriever_tool = Tool(
    name = "Cybersecurity Knowledgebase",
    description = "Searches and returns information regarding cybersecurity practices and procedures",
    func= knowledgebase_tool().run
)
