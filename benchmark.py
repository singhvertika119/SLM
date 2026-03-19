import ollama
import time

def run_benchmark(prompt: str, temperatures: list):
    print(f"--- Starting Benchmark for Llama 3.2 (3B) ---")
    print(f"Prompt: '{prompt}'\n")
    
    client = ollama.Client() 
    
    for temp in temperatures:
        print(f"Testing Temperature: {temp}...")
        
        start_time = time.time()
        
        response = client.generate(
            model='llama3.2',
            prompt=prompt,
            options={
                "temperature": temp
            },
            stream=False
        )
        
        end_time = time.time()
        
        tokens_generated = response.get('eval_count', 0)
        generation_time_sec = response.get('eval_duration', 0) / 1e9 
        
        tps = tokens_generated / generation_time_sec if generation_time_sec > 0 else 0
        
        print(f"Output: {response['response'].strip()}")
        print(f"Metrics: {tokens_generated} tokens | {generation_time_sec:.2f} seconds | {tps:.2f} TPS")
        print("-" * 40)

if __name__ == "__main__":
    test_prompt = "Write a short, creative haiku about a robot learning to code."
    test_temps = [0.0, 0.5, 1.0]
    
    run_benchmark(test_prompt, test_temps)