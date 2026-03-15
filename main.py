from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
import uvicorn
from pydantic import ValidationError

app = FastAPI(title="Local AI Assistant Engine")

# Define expected request payload
class GenerateRequest(BaseModel):
    prompt: str

# This defines the exact structure we want the LLM to return
class CharacterExtraction(BaseModel):
    name: str
    trait: str
    is_hero: bool

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
    
@app.post("/extract")
async def extract_character(request: GenerateRequest):
    client = ollama.AsyncClient()
    
    system_prompt = """
    You are a strict data extraction bot. Extract the main character from the user's prompt.
    You MUST respond ONLY in valid JSON matching this schema:
    {
        "name": "string",
        "trait": "string",
        "is_hero": boolean
    }
    """
    
    # store the evolving prompt in a variable
    current_prompt = f"{system_prompt}\n\nUser input: {request.prompt}"
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = await client.generate(
                model='llama3.2', 
                prompt=current_prompt,
                # Pass the Pydantic schema directly to the engine
                format=CharacterExtraction.model_json_schema(), 
                stream=False
            )
            
            raw_output = response['response']
            
            validated_data = CharacterExtraction.model_validate_json(raw_output)
            
            return {"status": "success", "attempts_needed": attempt + 1, "data": validated_data}
            
        except ValidationError as e:
            print(f"Attempt {attempt + 1} failed with error: {e}") 
            
            if attempt == max_retries - 1:
                raise HTTPException(status_code=422, detail=f"Failed after {max_retries} attempts. Last output: {raw_output}")
            
            error_feedback = f"\n\nYour previous JSON failed validation with this error:\n{e}\nFix the JSON keys and types and try again."
            current_prompt += error_feedback
            
    raise HTTPException(status_code=500, detail="Unexpected error in retry loop.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)