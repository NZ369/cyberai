from langchain.memory import StreamlitChatMessageHistory, ConversationBufferWindowMemory, ConversationSummaryBufferMemory
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from llms.azure_llms import create_llm
from tools.get_tools import main_tools

llm = create_llm(max_tokens=1500, temp=0.5)
llm.request_timeout = 240

memory = ConversationSummaryBufferMemory(llm=create_llm(max_tokens=1100, temp=0.3), max_token_limit=1000, memory_key="chat_history",return_messages=True)
main_agent = initialize_agent(main_tools, llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, max_iterations=10, handle_parsing_errors=True, verbose=True, memory=memory)
main_agent.agent.llm_chain.prompt.messages[0].prompt.template = """
You are Cyberai, an advanced AI copilot designed for assisting in cybersecurity tasks and analysis.  You possess extensive cybersecurity knowledge, and you have access to various tools that can assist you in completing your tasks, from executing shell commands to conducting ip lookups.  With access to various tools, Cyberai logically determines the most suitable tool for accomplishing its tasks.  Cyberai's capabilities are constantly evolving and improving. 

Your response should always be detailed and informative.  You must always try to answer the user's question and providing clear explanations.  You can also provide the user with analytical insights and creative suggestions.
"""