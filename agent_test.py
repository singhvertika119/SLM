import ollama
import psutil

# Define the OS-Level Tool
def get_system_stats(metric) -> str:
    """
    Get current system hardware metrics. Use this ONLY when the user asks about CPU, RAM, or battery.
    
    Args:
        metric: The specific hardware metric to check. MUST be one of: 'cpu', 'ram', 'battery'
    """
    # If the SLM accidentally passes a schema dictionary instead of a string, extract the value
    if isinstance(metric, dict):
        metric = metric.get('value', str(metric))
        
    # Ensure it is a lowercase string just in case the model capitalized it
    metric = str(metric).lower()

    if metric == 'cpu':
        cpu_usage = psutil.cpu_percent(interval=1)
        return f"CPU usage is at {cpu_usage}%."
        
    elif metric == 'ram':
        ram = psutil.virtual_memory()
        total_gb = round(ram.total / (1024 ** 3), 2)
        used_gb = round(ram.used / (1024 ** 3), 2)
        return f"RAM usage is at {ram.percent}%. Total RAM: {total_gb} GB. Used RAM: {used_gb} GB."
        
    elif metric == 'battery':
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery is at {battery.percent}%. Plugged in: {battery.power_plugged}"
        return "No battery detected."
        
    return f"Unknown metric requested: {metric}"

# Register the Tool
available_tools = {
    'get_system_stats': get_system_stats
}

def test_agent():
    # add a powerful System Prompt to override its refusal training
    messages = [
        {
            'role': 'system', 
            'content': 'You are a helpful, conversational AI assistant running locally on the user\'s hardware. When you receive data from a tool, you must synthesize it into a single, natural, and friendly sentence. CRITICAL: You must use the EXACT numbers provided by the tool. Do not do any math, do not convert units, and do not invent extra details.'
        },
        {'role': 'user', 'content': 'How much RAM is my computer using right now?'}
    ]
    
    print("User: How much RAM is my computer using right now?\n")
    
    # Send request with the new tool
    response = ollama.chat(
        model='llama3.2',
        messages=messages,
        tools=[get_system_stats] 
    )
    
    messages.append(response['message'])
    
    if response['message'].get('tool_calls'):
        for tool in response['message']['tool_calls']:
            function_to_call = available_tools[tool['function']['name']]
            kwargs = tool['function']['arguments']
            
            print(f"🤖 Action: LLM requested '{tool['function']['name']}' with args {kwargs}")
            
            # Execute the OS command
            result = function_to_call(**kwargs)
            print(f"⚙️ Local CPU: Tool returned -> {result}\n")
            
            messages.append({
                'role': 'tool',
                'content': str(result),
                'name': tool['function']['name']
            })
            
        print("🤖 LLM is reading the OS data and generating final response...")
        final_response = ollama.chat(model='llama3.2', messages=messages)
        print(f"\nFinal Answer: {final_response['message']['content']}")
    else:
        print("Model did not use a tool. It replied:")
        print(response['message']['content'])

if __name__ == "__main__":
    test_agent()