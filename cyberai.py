from langchain import PromptTemplate
from streamlit_extras.app_logo import add_logo
from agents.main_agent import main_agent
from PIL import Image
import streamlit as st

# Streamlit page configuration
st.set_page_config(
    page_title="Cyberai",
    page_icon="🤖",
    layout='wide'
)
image = Image.open('assets/logo.png')
st.image(image, width=500)
st.subheader("Cybersecurity Copilot")

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
        st.write(prompt)

# Generate response from AI
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = main_agent.invoke({"input": prompt})['output']
                print(response)
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
            except Exception as e:
                full_response = str(e)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    
hide_menu_style = """
        <style>
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)