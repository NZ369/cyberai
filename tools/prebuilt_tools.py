from langchain.tools import DuckDuckGoSearchRun, ShellTool
from langchain.utilities import WikipediaAPIWrapper
from langchain.utilities import PythonREPL
from langchain.agents.tools import Tool
from pydantic import BaseModel, Field
from llms.azure_llms import create_llm
from langchain.chains import LLMMathChain

llm = create_llm(max_tokens=2000, temp=0)

python_repl = PythonREPL()
python_tool = Tool(
    name='Python code interpretor',
    func=python_repl.run,
    description="Useful for executing python code. You should input python code."
)

wikipedia = WikipediaAPIWrapper()
wikipedia_tool = Tool(
    name='Wikipedia',
    func= wikipedia.run,
    description="Useful for getting background info on a topic, country or person on wikipedia"
)

search = DuckDuckGoSearchRun()
duckduckgo_tool = Tool(
    name='DuckDuckGo Search',
    func= search.run,
    description="Useful for when you need to do a search on the internet about anything"
)

llm_math_chain = LLMMathChain(llm=llm, verbose=True)
calculator_tool = Tool(
        name="Calculator",
        func=llm_math_chain.run,
        description="Useful for when you need to answer questions about math.",
)

shell_tool = ShellTool()
shell_tool.description = shell_tool.description + f"args {shell_tool.args}".replace(
    "{", "{{"
).replace("}", "}}")