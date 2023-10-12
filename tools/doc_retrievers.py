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

# Define a data model for the document input
class DocumentInput(BaseModel):
    question: str = Field()
    
main_retriever_tool = Tool(
                    args_schema=DocumentInput,
                    name="Cybersecurity Knowledgebase",
                    description="Searches and returns information regarding cybersecurity practices and procedures.",
                    func=RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever(search_kwargs={'k': 3})),
                    # return_source_documents=True
                )