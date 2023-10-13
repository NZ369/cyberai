import os
import openai, langchain, pinecone
from llms.azure_llms import create_azure_embedder, create_llm
from langchain.document_loaders import DirectoryLoader, UnstructuredPDFLoader, OnlinePDFLoader, PyPDFLoader
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

#load environment variables
load_dotenv()

PINECONE_API_KEY= os.getenv("PINECONE_API_KEY")
PINECONE_ENV = "us-west4-gcp-free"

index_name = 'cyberai'

def parse_response(response):
    print(response['result'])
    print('\n\nSources:')
    for source_name in response["source_documents"]:
        print(source_name.metadata['source'], "page #:", source_name.metadata['page'])

try:
    pinecone.init(
    api_key = PINECONE_API_KEY,
    environment = PINECONE_ENV
    )
    loader = DirectoryLoader('./data', glob="**/*.txt", show_progress=True)
    docs = loader.load()
    print(len(docs))
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    texts = text_splitter.split_documents(docs)

    embeddings = create_azure_embedder()
    docsearch = Pinecone.from_documents(texts, embeddings, index_name = index_name)
    retriever = docsearch.as_retriever(include_metadata=True, metadata_key = 'source')
except Exception as e:
    print(e)