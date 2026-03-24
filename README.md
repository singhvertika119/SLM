# KOKO- Local Offline AI Engine & Multimodal Assistant

A production-grade, 100% offline AI architecture built with Python. This project utilizes Ollama for local LLM inference, FastAPI for an asynchronous API gateway with strict structured output parsing, and Streamlit for a stateful multimodal chat interface. 

## 🏗️ Architecture Overview
This repository contains three decoupled components that all interface with a central local inference engine:
1. **API Gateway (`main.py`)**: An async FastAPI backend that enforces strict Pydantic JSON schemas on LLM outputs using Structured Decoding.
2. **Multimodal Chat UI (`chat_app.py`)**: A Streamlit frontend that maintains conversational memory and handles image ingestion for Vision-Language processing.
3. **Diagnostics (`benchmark.py`)**: A standalone script to measure model Tokens Per Second (TPS) and test temperature variances.

## 🚀 Features
- **Zero Cloud Dependency:** Runs entirely on local hardware. No API keys, no internet required, and 100% data privacy.
- **Multimodal Computer Vision:** Integrates `moondream`, a highly optimized 1.7GB Vision-Language Model (VLM), allowing the assistant to analyze and reason about local images.
- **Structured JSON Extraction:** Uses Schema-Guided Generation to force the LLM to output valid JSON matching exact data models.
- **Asynchronous Inference:** Prevents blocking the main thread during heavy token generation.
- **Self-Correcting Retry Loop:** Gracefully catches LLM hallucinations and feeds errors back into the prompt for self-correction.
<img width="900" height="900" alt="image" src="https://github.com/user-attachments/assets/eeec1894-c0da-4988-816a-0ae51e6507fb" />
