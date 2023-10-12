import time
from streamlit_extras.app_logo import add_logo
from PIL import Image
from langchain.callbacks import StreamlitCallbackHandler
import streamlit as st

from langchain.tools.render import render_text_description
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentExecutor
from langchain import hub
from llms.azure_llms import create_llm
from tools.get_tools import main_tools

############ MAIN AGENT << START >> ############

llm = create_llm(max_tokens=2400, temp=0.5)
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

memory = ConversationBufferWindowMemory(memory_key="chat_history", k=3, return_messages=True)
main_agent = AgentExecutor(agent=agent, tools=main_tools, max_iterations=10, verbose=True, memory=memory)

############ MAIN AGENT << END >> ############

# Streamlit page configuration
st.set_page_config(
    page_title="Cyberai",
    page_icon="🤖",
    layout='wide'
)
image = Image.open('assets/logo.png')
st.image(image, width=500)
st.subheader("Cybersecurity Copilot")

# Initializing Memory
if "memory" not in st.session_state:
    st.session_state.memory = memory

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

with st.sidebar:
    add_logo("assets/logo2.png", height=50)
    st.title('Cyberai')
    st.markdown('''
    ## About
    Cyberai is a smart AI assistant for cyber security analysts.
    ''')
    st.button('Clear Chat History', on_click=clear_chat_history)
        
# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate the assistant's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Set up the Streamlit callback handler
                st_callback = StreamlitCallbackHandler(st.container())
                message_placeholder = st.empty()
                full_response = ""
                assistant_response = main_agent.run(prompt, callbacks=[st_callback])

                # Simulate a streaming response with a slight delay
                for chunk in assistant_response.split():
                    full_response += chunk + " "
                    time.sleep(0.05)

                    # Add a blinking cursor to simulate typing
                    message_placeholder.markdown(full_response + "▌")
                
                # Display the full response
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = str(e)

    # Add the assistant's response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
hide_menu_style = """
        <style>
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)