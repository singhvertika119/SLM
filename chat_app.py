import streamlit as st
import ollama

# Set up the page layout
st.set_page_config(page_title="Offline AI", page_icon="🤖")
st.title("KOKO")

# 1. Initialize the session state to store our conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Render the existing chat history to the screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Create the input box for the user
if prompt := st.chat_input("Type your message here..."):
    
    # Add the new user message to the history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4. Generate the response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Notice we use ollama.chat() instead of generate(), 
            # and we pass the ENTIRE messages array, not just the single prompt.
            response = ollama.chat(model='llama3.2', messages=st.session_state.messages)
            
            # Extract the text and display it
            bot_reply = response['message']['content']
            st.markdown(bot_reply)
            
    # 5. Save the bot's reply to the history so it remembers it for next time
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})