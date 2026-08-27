"""Builds Chroma vector index from textile domain knowledge raw documents."""

import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.agent.rag_indexer import KnowledgeIndexer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    docs_dir = "data/knowledge/raw"
    persist_dir = "data/chroma_db"

    if not os.path.exists(docs_dir):
        logger.error(f"Knowledge raw directory not found at {docs_dir}")
        return

    logger.info(f"Building knowledge index from {docs_dir}...")
    indexer = KnowledgeIndexer(persist_directory=persist_dir)
    indexer.index_directory(docs_dir)
    logger.info(f"Knowledge index built successfully in {persist_dir}")


if __name__ == "__main__":
    main()
