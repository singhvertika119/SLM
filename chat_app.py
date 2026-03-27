import streamlit as st
import ollama
import psutil
import json
import sqlite3
import re

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

def query_local_db(sql_query: str) -> str:
    """
    Query the local inventory database.
    
    Args:
        sql_query: The SQL SELECT command.
    """
    raw_input = str(sql_query)
    
    # --- UPGRADED REGEX ARMOR ---
    # Starts at SELECT, grabs everything until it hits a double-quote or curly brace
    # at the very end of the JSON wrapper, safely ignoring the single quotes inside the SQL!
    match = re.search(r"(SELECT\s+.*?(?=\"|\}|$))", raw_input, re.IGNORECASE)
    
    if match:
        clean_query = match.group(1).strip()
    else:
        clean_query = raw_input.replace('```sql', '').replace('```', '').strip()
    # -----------------------------

    if not clean_query.lower().startswith('select'):
        return f"Error: Could not find a valid SELECT query. I saw: {raw_input}"

    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute(clean_query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No results found for that item."
            
        return f"Database results: {rows}"
    except sqlite3.Error as e:
        # Debugging upgrade: Show us exactly what string caused the error!
        return f"SQL Error: {str(e)} | Query Attempted: [{clean_query}]"

# Register the new tool alongside the OS monitor
available_tools = {
    'get_system_stats': get_system_stats,
    'query_local_db': query_local_db
}


# --- 2. Initialize State & System Prompt ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            'role': 'system', 
            'content': (
                "You are an advanced local AI assistant. "
                "DATABASE SCHEMA: You have access to an SQLite database with a table named 'inventory'. "
                "Columns: id (INTEGER), item_name (TEXT), quantity (INTEGER), price (REAL). "
                "CRITICAL RULES: "
                "1. When asked about stock or prices, DO NOT use JSON tools. Write a valid SQL SELECT statement wrapped exactly in <SQL> and </SQL> tags. "
                "2. Always use the LIKE operator with % wildcards for text searches (e.g., WHERE item_name LIKE '%Samsung%'). Do not use exact = matches."
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
            
            # --- INTENT ROUTER (The Hybrid Bouncer) ---
            tools_to_pass = None
            if model_to_use == 'llama3.2':
                status.update(label="Classifying intent...", state="running")
                
                user_text = prompt.lower()
                
                # Check for Hardware Intent
                if any(word in user_text for word in ['ram', 'cpu', 'battery']):
                    st.write("🔍 Intent: Hardware query. Unlocking System Monitor.")
                    tools_to_pass = [available_tools['get_system_stats']]
                    
                # Check for Database Intent
                elif any(word in user_text for word in ['inventory', 'stock', 'price', 'database', 'items', 'how many']):
                    st.write("🗄️ Intent: Database query. Triggering XML SQL Engine.")
                    # THE FIX: We MUST keep tools locked here! 
                    # If we pass the tool object, Ollama forces JSON and ruins our XML strategy.
                    tools_to_pass = None 
                    
                else:
                    st.write("💬 Intent: General chat. Tools locked.")
            # -----------------------------------
            # -----------------------------------
            # Step 1: Initial Inference
            response = ollama.chat(
                model=model_to_use, 
                messages=st.session_state.messages,
                tools=tools_to_pass 
            )
            
            # --- THE XML TAG SNIPER ---
            bot_text = response['message'].get('content', '')
            
            # If the model wrote <SQL> tags in the chat, we intercept it!
            if '<SQL>' in bot_text.upper():
                st.write("🔧 Snipping SQL from XML tags...")
                
                # Extract everything between <SQL> and </SQL>
                match = re.search(r"<SQL>(.*?)</SQL>", bot_text, re.IGNORECASE | re.DOTALL)
                
                if match:
                    extracted_sql = match.group(1).strip()
                    st.write(f"⚙️ Running DB Query: `{extracted_sql}`")
                    
                    # Run the database function directly
                    db_result = query_local_db(extracted_sql)
                    st.write(f"📊 Result: {db_result}")
                    
                    # Feed the result back into the LLM's memory as a tool response
                    st.session_state.messages.append({
                        'role': 'tool', 
                        'content': str(db_result), 
                        'name': 'query_local_db'
                    })
                    
                    # Wipe the SQL tags from the UI so it looks clean
                    response['message']['content'] = ""
                    # Ensure the broken JSON tool_calls array is empty
                    response['message']['tool_calls'] = []
            # --------------------------
            
            # --- THE "SILENCER" FIX (Kept for the Hardware Tool) ---
            elif response['message'].get('tool_calls'):
                response['message']['content'] = ""
            # --------------------------
            
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