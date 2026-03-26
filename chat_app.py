import streamlit as st
import ollama
import psutil
import json

st.set_page_config(page_title="Local Agent", page_icon="🙈")
st.title("KOKO")

# Define the Tool & Defensive Logic
def get_system_stats(metric: str = "all") -> str:
    """
    Get current system hardware metrics. Use this when the user asks about CPU, RAM, or battery.
    
    Args:
        metric: The specific hardware metric to check. MUST be one of: 'cpu', 'ram', 'battery', or 'all'
    """
    # Convert whatever weird format the LLM passes into a lowercase string
    metric_str = str(metric).lower()

    # Pre-calculate all metrics
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    total_gb = round(ram.total / (1024 ** 3), 2)
    used_gb = round(ram.used / (1024 ** 3), 2)
    battery = psutil.sensors_battery()
    batt_str = f"Battery: {battery.percent}% plugged in: {battery.power_plugged}" if battery else "No battery detected."

    # If the LLM perfectly asks for one thing, give it that one thing
    if metric_str == 'cpu':
        return f"CPU usage is at {cpu_usage}%."
    elif metric_str == 'ram':
        return f"RAM usage is at {ram.percent}%. Total RAM: {total_gb} GB. Used RAM: {used_gb} GB."
    elif metric_str == 'battery':
        return batt_str
        
    # If it passes a schema dict, asks for "ram and cpu", or panics,
    # just return all the hardware data and let the LLM filter it for the user
    return f"CPU usage is at {cpu_usage}%. RAM usage is at {ram.percent}% (Used: {used_gb} GB / Total: {total_gb} GB). {batt_str}"
available_tools = {'get_system_stats': get_system_stats}

# Initialize State & System Prompt
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            'role': 'system', 
            'content': (
                "You are a helpful AI assistant running locally on the user's hardware. "
                "CRITICAL RULES: "
                "1. ONLY use your system tools if the user EXPLICITLY asks about their hardware (RAM, CPU, battery). "
                "2. If the user asks a general knowledge question or just wants to chat, DO NOT use any tools. Answer normally based on your training data. "
                "3. When you DO use a tool, you must use the EXACT numbers provided. Do not invent details."
            )
        }
    ]

# Sidebar for Vision ---
with st.sidebar:
    st.header("Visual Input")
    uploaded_file = st.file_uploader("Upload an image (Uses Moondream)", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Ready for analysis")

# Render Chat History
# We skip rendering 'system' and 'tool' messages so the UI stays clean,
# but they remain in session_state so the AI can read them.
for message in st.session_state.messages:
    if message["role"] in ["system", "tool"]:
        continue 
    
    if message["role"] == "assistant" and message.get("tool_calls"):
        continue

    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "images" in message and message["images"]:
            st.image(message["images"][0], width=300) 

# Main Chat & Agent Loop
if prompt := st.chat_input("Ask about your RAM, upload an image, or just chat..."):
    
    user_msg = {"role": "user", "content": prompt}
    
    # Model Router: Use Moondream if there's an image, otherwise use Llama 3.2
    if uploaded_file is not None:
        user_msg["images"] = [uploaded_file.getvalue()]
        model_to_use = 'moondream' 
    else:
        model_to_use = 'llama3.2'

    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file is not None:
            st.image(uploaded_file, width=300)

    with st.chat_message("assistant"):
        # Create a visual "Thinking" container
        with st.status("Thinking...", expanded=True) as status:
            
            # INTENT ROUTER (The Deterministic Bouncer)
            tools_to_pass = None
            if model_to_use == 'llama3.2':
                status.update(label="Classifying intent...", state="running")
                
                # We abandon the LLM for routing and use 100% reliable Python logic
                hardware_keywords = ['ram', 'cpu', 'battery', 'memory', 'hardware', 'system']
                is_hardware = any(word in prompt.lower() for word in hardware_keywords)
                
                if is_hardware:
                    st.write("🔍 Intent: Hardware query detected by keyword. Unlocking tools.")
                    tools_to_pass = [available_tools['get_system_stats']]
                else:
                    st.write("💬 Intent: General chat detected. Tools locked.")
            
            status.update(label="Generating response...", state="running")

            # Initial Inference
            response = ollama.chat(
                model=model_to_use, 
                messages=st.session_state.messages,
                tools=tools_to_pass 
            )
            
            # If the model triggers a tool, we wipe any text it tries to yap out.
            # This prevents it from polluting the chat history with hallucinations like "type php".
            if response['message'].get('tool_calls'):
                response['message']['content'] = ""
            
            st.session_state.messages.append(response['message'])
            
            # Intercept Tool Calls
            if response['message'].get('tool_calls'):
                status.update(label="Executing local OS tools...", state="running")
                
                for tool in response['message']['tool_calls']:
                    func_name = tool['function']['name']
                    kwargs = tool['function']['arguments']
                    
                    st.write(f"⚙️ Running `{func_name}` with args: {kwargs}")
                    
                    if func_name in available_tools:
                        result = available_tools[func_name](**kwargs)
                        st.write(f"📊 Result: {result}")
                        
                        st.session_state.messages.append({
                            'role': 'tool',
                            'content': str(result),
                            'name': func_name
                        })
                
                status.update(label="Synthesizing final response...", state="running")
                
                # Final Inference with Tool Data
                final_response = ollama.chat(model=model_to_use, messages=st.session_state.messages)
                bot_reply = final_response['message']['content']
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
                status.update(label="Done!", state="complete", expanded=False)
                st.markdown(bot_reply)
                
            else:
                # Standard text or vision response (No tools used)
                bot_reply = response['message']['content']
                status.update(label="Done!", state="complete", expanded=False)
                st.markdown(bot_reply)