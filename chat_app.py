import streamlit as st
import ollama

st.set_page_config(page_title="Local  AI", page_icon="👁️")
st.title("KOKO")

# 1. Add a file uploader to the sidebar
with st.sidebar:
    st.header("Visual Input")
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Ready for analysis")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Render the chat history (including images from past messages)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If the user's message contained an image, display it in the chat log
        if "images" in message and message["images"]:
            st.image(message["images"][0], width=300) 

# 3. Handle new user input
if prompt := st.chat_input("Ask a question about the image, or just chat..."):
    
    # Construct the base message
    user_msg = {"role": "user", "content": prompt}
    
    # If an image is currently uploaded in the sidebar, attach its bytes to the message
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        # The ollama library expects a list of images for a single message
        user_msg["images"] = [image_bytes]

    # Add to UI state and display
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file is not None:
            st.image(uploaded_file, width=300)

    # 4. Generate the multimodal response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing pixels and text..."):
            # Ensure we are calling the vision model!
            response = ollama.chat(model='moondream', messages=st.session_state.messages)
            
            bot_reply = response['message']['content']
            st.markdown(bot_reply)
            
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})