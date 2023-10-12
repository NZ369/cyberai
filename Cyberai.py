import os
import time
from streamlit_extras.app_logo import add_logo
from agents.main_agent import main_agent
from streamlit_extras.add_vertical_space import add_vertical_space
from langchain.callbacks import StreamlitCallbackHandler
from PIL import Image
import streamlit as st
from datetime import datetime


import streamlit as st
from streamlit_feedback import streamlit_feedback
from langchain.callbacks.tracers.run_collector import RunCollectorCallbackHandler
from langchain.memory import StreamlitChatMessageHistory, ConversationBufferMemory
from langchain.schema.runnable import RunnableConfig
from langsmith import Client
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
import os

from tools.local_qa_tools import create_qa_retriever

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "ls__db5db378bb5a4d1780f19e08eb528f22"
os.environ["LANGCHAIN_PROJECT"] = "cyberai"

# Streamlit page configuration
st.set_page_config(
    page_title="Cyberai",
    page_icon="🤖",
    layout='wide'
)
image = Image.open('assets/logo.png')
st.image(image, width=500)
st.subheader("Cybersecurity Copilot")
download_str = []

# Store LLM generated responses
if "messages" not in st.session_state.keys() or len(st.session_state.messages) == 0:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    st.session_state.trace_link = None
    st.session_state.run_id = None

with st.sidebar:
    add_logo("assets/logo2.png", height=50)
    st.title('Cyberai')
    st.markdown('''
    ## About
    Cyberai is a smart AI assistant for cyber security analysts.
    ''')
    add_vertical_space(1)
    st.subheader("Chat with your local documents")
    pdf_docs = st.file_uploader("Select your PDFs here", accept_multiple_files=True)
    if st.button("Submit", use_container_width=True):
        with st.spinner("Processing"):
            create_qa_retriever(pdf_docs, type="azure", database="FAISS")
        st.success("Embeddings completed.", icon="✅")
    add_vertical_space(2)
    st.button('Clear Chat History', on_click=clear_chat_history, type="primary", use_container_width=True)
   
# User-provided prompt
if prompt := st.chat_input(placeholder="Need help? Just ask."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    download_str.append("User: "+prompt)
    
# Generate response from AI
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        try:
            # Set up the Streamlit callback handler
            st_callback = StreamlitCallbackHandler(st.container())
            message_placeholder = st.empty()
            full_response = ""
            if prompt == "":
                prompt = "Tell me a fun cybersecurity fact"
            assistant_response = main_agent.run(prompt, callbacks=[st_callback])

            # Simulate a streaming response with a slight delay
            input_dict = {"input": prompt}
            for chunk in assistant_response.split():
                full_response += chunk + " "
                time.sleep(0.05)

                # Add a blinking cursor to simulate typing
                message_placeholder.markdown(full_response + "▌")
            
            # Display the full response
            message_placeholder.write(full_response)
        except Exception as e:
            full_response = str(e)
            
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    download_str.append("AI: "+full_response)
    
    # with collect_runs as cb: works with chains
    feedback_option = "faces"
    feedback = streamlit_feedback(
            feedback_type=feedback_option,
            optional_text_label="[Optional] Your feedback helps to improve the AI :D"
    )
    
# Download conversation
# Get current date and time
now = datetime.now()
formatted_now = now.strftime("%Y-%m-%d-%H-%M")
download_filename = "Cyberai Chat "+formatted_now

with st.sidebar:
    download_str = '\n\n'.join(download_str)
    if download_str:
        st.download_button('Download Chat',download_str,download_filename, use_container_width=True)
                    
hide_menu_style = """
        <style>
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)