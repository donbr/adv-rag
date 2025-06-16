"""
Retrieval-Augmented Generation (RAG) system components for the Advanced RAG project.

This package contains all RAG-related functionality:
- Embedding models and vector representations (embeddings.py)
- Vector store setup and management (vectorstore.py)
- Document retrieval logic (retriever.py)
- RAG chain construction and orchestration (chain.py)
- Document processing and data loading (data_loader.py)

Educational Note: This separation allows learners to understand each RAG
component independently - embeddings, vector storage, retrieval, and
chain orchestration - before seeing how they work together as a complete
RAG system. Each module demonstrates a core RAG concept.
"""

__version__ = "1.0.0" 