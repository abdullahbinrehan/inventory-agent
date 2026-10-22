"""
RAG (Retrieval-Augmented Generation) engine.
Uses ChromaDB (in-memory) for vector storage and Groq for answering.
"""

import os
import json
import logging
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from groq import Groq
from agent import config

logger = logging.getLogger(__name__)

# Use a free, local embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def _load_documents() -> list[Document]:
    """Read current inventory and history to create context documents."""
    docs = []
    
    # 1. Load current state (inventory alerts)
    state_file = config.STATE_FILE
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = json.load(f)
            for sku, record in state_data.items():
                text = (
                    f"Inventory Item: {sku}. "
                    f"Urgency: {record.get('urgency', 'UNKNOWN')}. "
                    f"Alerts in last 7 days: {record.get('alert_count_7d', 0)}. "
                    f"Last alerted at: {record.get('last_alerted_at', 'Never')}."
                )
                docs.append(Document(page_content=text, metadata={"type": "current_inventory"}))

    # 2. Load history (CSV)
    history_file = config.PROJECT_ROOT / "docs" / "run_history.csv"
    if history_file.exists():
        df = pd.read_csv(history_file)
        # Convert the last 30 rows to text
        for _, row in df.tail(30).iterrows():
            text = (
                f"Run Date: {row['date']}. Source: {row['source']}. "
                f"Total SKUs: {row['total_skus']}. Alertable: {row['alertable']}. "
                f"Critical: {row['critical']}. Digest: {row['digest']}."
            )
            docs.append(Document(page_content=text, metadata={"type": "history"}))
            
    return docs

def rebuild_vector_store():
    """Builds the ChromaDB database in memory and returns it."""
    docs = _load_documents()
    if not docs:
        return None
        
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    # Build in-memory ChromaDB (no disk writes = no Windows file locks)
    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
    logger.info("Built in-memory ChromaDB with %d documents", len(docs))
    return vectorstore

def ask_inventory(question: str, vectorstore) -> str:
    """Retrieve context and ask Groq to answer the question."""
    if not vectorstore:
        return "Please click 'Sync Knowledge Base' first to load your data."

    # Find the 5 most relevant pieces of text
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    docs = retriever.invoke(question)
    
    context = "\n\n".join([d.page_content for d in docs])
    
    prompt = f"""You are an expert inventory management assistant for an e-commerce store.
Use ONLY the following context to answer the user's question. If the answer isn't in the context, say "I don't have enough data to answer that."

IMPORTANT FORMATTING RULES:
- DO NOT use markdown tables.
- Present data using clean bullet points or short paragraphs.
- Be concise and conversational.

Context:
{context}

User Question: {question}
"""
    
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Groq failed for chat: %s", e)
        return f"Sorry, I encountered an error connecting to the LLM: {e}"