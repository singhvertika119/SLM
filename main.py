from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
import uvicorn

app = FastAPI(title="Local AI Assistant Engine")

# Define expected request payload
class GenerateRequest(BaseModel):
    prompt: str

@app.get("/health")
async def health_check():
    return {"status": "running", "engine": "FastAPI + Ollama"}

@app.post("/generate")
async def generate_text(request: GenerateRequest):
    try:
        # Initialize the Async client
        client = ollama.AsyncClient()
        
        # Call the model
        # stream=False means we wait for the entire response before returning it
        response = await client.generate(
            model='llama3.2', 
            prompt=request.prompt,
            stream=False
        )
        
        return {"response": response['response']}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)