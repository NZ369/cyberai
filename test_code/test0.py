

#######################################

import os
import time
from streamlit_extras.app_logo import add_logo
from streamlit_extras.add_vertical_space import add_vertical_space
from langchain.callbacks import StreamlitCallbackHandler
from PIL import Image
import streamlit as st
from datetime import datetime


import streamlit as st
from streamlit_feedback import streamlit_feedback
from langchain.callbacks.manager import collect_runs
from langchain.callbacks.tracers.run_collector import RunCollectorCallbackHandler
from langchain.memory import StreamlitChatMessageHistory, ConversationBufferMemory
from langchain.schema.runnable import RunnableConfig
from langsmith import Client
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
import os

from tools.local_qa_tools import create_qa_retriever
import time
from streamlit_extras.app_logo import add_logo
from PIL import Image
from langchain.schema import ChatMessage
from langchain.callbacks import StreamlitCallbackHandler
import streamlit as st
from langchain.memory import StreamlitChatMessageHistory
from langchain.tools.render import render_text_description
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.memory import ConversationSummaryBufferMemory
from langchain.agents import AgentExecutor
from langchain import hub
from llms.azure_llms import create_llm
from tools.get_tools import main_tools

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

memory = ConversationSummaryBufferMemory(chat_memory=StreamlitChatMessageHistory(key="messages"),llm=create_llm(max_tokens=1100, temp=0.3), max_token_limit=1000, memory_key="chat_history",return_messages=True)
main_agent = AgentExecutor(agent=agent, tools=main_tools, max_iterations=10, verbose=True, memory=memory)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "ls__db5db378bb5a4d1780f19e08eb528f22"
os.environ["LANGCHAIN_PROJECT"] = "cyberai"
#client = Client(api_url="https://api.smith.langchain.com", api_key="ls__db5db378bb5a4d1780f19e08eb528f22")

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
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [ChatMessage(role="assistant", content="How can I help you?")]

# Display chat messages
for msg in st.session_state.messages:
    avatar = "🦜" if msg.type == "assistant" else None
    with st.chat_message(msg.type, avatar=avatar):
        st.markdown(msg.content)
        
def clear_chat_history():
    st.session_state.messages = [ChatMessage(role="assistant", content="How can I help you?")]
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
   
if prompt := st.chat_input(placeholder="Ask me a question!"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    download_str.append("User: "+prompt)
    
    with st.chat_message("assistant", avatar="🦜"):
        message_placeholder = st.empty()
        full_response = ""

        input_dict = {"input": prompt}
        with collect_runs() as cb:
            for chunk in main_agent.stream(input_dict, config={"tags": ["Cyberai chat"]}):
                print(chunk)
                full_response += chunk['output']
                message_placeholder.markdown(full_response + "▌")
            run_id = cb.traced_runs[0].id
        message_placeholder.markdown(full_response)
        
        message = ChatMessage(role="assistant", content=full_response)
        st.session_state.messages.append(message)
        download_str.append("AI: "+full_response)
        
        if run_id:
            feedback_option="faces"
            feedback = streamlit_feedback(
                feedback_type=feedback_option,
                optional_text_label="[Optional] Please provide an explanation",
                key=f"feedback_{run_id}",
            )

            # Define score mappings for both "thumbs" and "faces" feedback systems
            score_mappings = {
                "thumbs": {"👍": 1, "👎": 0},
                "faces": {"😀": 1, "🙂": 0.75, "😐": 0.5, "🙁": 0.25, "😞": 0},
            }

            # Get the score mapping based on the selected feedback option
            scores = score_mappings[feedback_option]

            if feedback:
                # Get the score from the selected feedback option's score mapping
                score = scores.get(feedback["score"])

                if score is not None:
                    # Formulate feedback type string incorporating the feedback option
                    # and score value
                    feedback_type_str = f"{feedback_option} {feedback['score']}"

                    # Record the feedback with the formulated feedback type string
                    # and optional comment
                    client = Client(api_url="https://api.smith.langchain.com", api_key="ls__db5db378bb5a4d1780f19e08eb528f22")
                    
                    feedback_record = client.create_feedback(
                        run_id,
                        feedback_type_str,
                        score=score,
                        comment=feedback.get("text"),
                    )
                    st.session_state.feedback = {
                        "feedback_id": str(feedback_record.id),
                        "score": score,
                    }
                else:
                    st.warning("Invalid feedback score.")
        
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