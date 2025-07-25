# SmartBot

# 🤖 SmartAgent LLM App

A modular AI agent powered by LLMs, Pinecone vector database, and synthetic data pipelines. This project enables efficient query processing, dynamic data updates, and scalable automation—all in one Python-based solution. The project has a textbook which use as knowledge base for answering medical related question such "What is the symptoms of Rabbis? "

---

## 📦 Features

- 🔌 Plug-and-play LLM integration (e.g., OpenAI, Cohere)
- 📚 Vector database setup using Pinecone
- 🔄 Synthetic data fetch and update flow
- 🧠 Intelligent agent for inference and automation
- ⚙️ Environment-configurable and modular codebase

---

## 🚀 How to Use

1. **Set Environment Variables**

   Define the following environment variables:

   - `XXX_API_KEY`: API key for your preferred LLM provider  
   - `PINECONE_API_KEY`: Pinecone API key  
   - `WORKDIR`: Root directory of the repository

2. **Initialize the Vector Database**  
   Run once to create the database:
        python vector_database/main.py

3. **Update Synthetic Data**
    Refresh availability data:
        python synthetic_data/get_availability.py

4. **Update Synthetic Data**
    Start the app:
        python agent.py
4. **Requirements**
        pip install -r requirements.txt
