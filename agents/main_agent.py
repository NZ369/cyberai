from langchain.tools.render import render_text_description
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.memory import ConversationSummaryBufferMemory
from langchain.agents import AgentExecutor
from langchain import hub
from llms.azure_llms import create_llm
from tools.get_tools import main_tools

llm = create_llm(max_tokens=1700, temp=0.5)
llm.request_timeout = 240

prompt = hub.pull("veice/react-cyber-assistant")

prompt = prompt.partial(
    tools=render_text_description(main_tools),
    tool_names=", ".join([t.name for t in main_tools]),
)

llm_with_stop = llm.bind(stop=["\nObservation"])

agent = {
    "input": lambda x: x["input"],
    "agent_scratchpad": lambda x: format_log_to_str(x['intermediate_steps']),
    "chat_history": lambda x: x["chat_history"]
} | prompt | llm_with_stop | ReActSingleInputOutputParser()

memory = ConversationSummaryBufferMemory(llm=create_llm(max_tokens=1100, temp=0.3), max_token_limit=1000, memory_key="chat_history", return_messages=True)
main_agent = AgentExecutor(agent=agent, tools=main_tools, max_iterations=10, verbose=True, memory=memory)