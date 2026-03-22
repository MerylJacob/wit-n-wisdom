from pydantic_settings import BaseSettings
from typing import List, Dict

AUSTEN_BOOKS = [
    {
        "title": "Pride and Prejudice",
        "url": "https://www.gutenberg.org/files/1342/1342-0.txt",
        "filename": "pride_and_prejudice.txt",
        "start_marker": "Chapter I",
    },
    {
        "title": "Sense and Sensibility",
        "url": "https://www.gutenberg.org/files/161/161-0.txt",
        "filename": "sense_and_sensibility.txt",
        "start_marker": "CHAPTER I",
    },
    {
        "title": "Emma",
        "url": "https://www.gutenberg.org/files/158/158-0.txt",
        "filename": "emma.txt",
        "start_marker": "CHAPTER I",
    },
    {
        "title": "Persuasion",
        "url": "https://www.gutenberg.org/files/105/105-0.txt",
        "filename": "persuasion.txt",
        "start_marker": "Chapter 1",
    },
    {
        "title": "Northanger Abbey",
        "url": "https://www.gutenberg.org/files/121/121-0.txt",
        "filename": "northanger_abbey.txt",
        "start_marker": "Chapter 1",
    },
    {
        "title": "Mansfield Park",
        "url": "https://www.gutenberg.org/files/141/141-0.txt",
        "filename": "mansfield_park.txt",
        "start_marker": "Chapter I",
    },
]


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "llama3"
    embed_model: str = "nomic-embed-text"
    chroma_path: str = "./chroma_db"
    collection_name: str = "austen_complete"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5

    class Config:
        env_file = ".env"


settings = Settings()