# KOKO- Local Offline AI Engine & Multimodal AI Agent

A 100% local, privacy-first AI assistant capable of multimodal vision, live system monitoring, and Text-to-SQL database querying. Built with Streamlit, Ollama, and defensive Python engineering.

This project goes beyond basic API wrappers by implementing deterministic intent routing, tool-calling loops, and regex-based output parsing to wrangle Small Language Models (SLMs) and prevent hallucinations. 

## 🧠 Architecture Stack

* **Frontend:** Streamlit
* **LLM Backend:** Ollama
* **Core Logic Model:** `llama3.2` (3B Parameters)
* **Vision Model:** `moondream` (1.8B Parameters)
* **System Tools:** `psutil`, `sqlite3`, `re` (Regex)

## ✨ Key Features

* **100% Offline & Private:** Powered entirely by local models running via Ollama. No data ever leaves your machine.
* **Multimodal Vision Router:** Automatically detects image uploads and routes the prompt to the `moondream` Vision-Language Model for analysis.
* **Deterministic Intent Routing (The Bouncer):** Uses zero-latency Python keyword matching to bypass LLM routing hallucinations, securely locking or unlocking system tools based on user intent.
* **Live System Monitor:** Intercepts hardware queries to execute local `psutil` commands, feeding real-time CPU, RAM, and Battery data back into the LLM's context window.
* **Text-to-SQL Engine (XML Tag Sniper):** Bypasses fragile JSON tool-calling schemas by forcing the LLM to write SQL within `<SQL>` tags. A Python regex sniper extracts the code, runs it against a local SQLite database, and returns the natural language result.
<img width="500" height="500" alt="image" src="https://github.com/user-attachments/assets/eeec1894-c0da-4988-816a-0ae51e6507fb" />
<img width="500" height="500" alt="Screenshot 2026-03-24 203019" src="https://github.com/user-attachments/assets/485bbbae-e559-406f-9206-7036dc70f720" />

