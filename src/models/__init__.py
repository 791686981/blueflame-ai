"""
Agent models public API

便捷导出：
- LLM：get_llm, register_custom_model, ModelConfig, ModelProvider
- Embedding：get_embedding_model, register_custom_embedding, EmbeddingModelConfig, EmbeddingProvider
"""

# LLMs
from .llms import (
    get_llm,
    register_custom_model,
    ModelConfig,
    ModelProvider,
    llm_manager,
)

# Embeddings
from .embeddings import (
    get_embedding_model,
    register_custom_embedding,
    EmbeddingModelConfig,
    EmbeddingProvider,
    embedding_manager,
)

__all__ = [
    # LLMs
    "get_llm",
    "register_custom_model",
    "ModelConfig",
    "ModelProvider",
    "llm_manager",
    # Embeddings
    "get_embedding_model",
    "register_custom_embedding",
    "EmbeddingModelConfig",
    "EmbeddingProvider",
    "embedding_manager",
]
