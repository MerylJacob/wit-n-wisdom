import os
import urllib.request
from tqdm import tqdm
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from app.config import settings, AUSTEN_BOOKS


def download_book(book: dict, data_dir: str) -> str:
    """Download a book from Project Gutenberg if not already present."""
    filepath = os.path.join(data_dir, book["filename"])
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"  Already downloaded: {book['title']}")
        return filepath
    print(f"  Downloading: {book['title']}...")
    urllib.request.urlretrieve(book["url"], filepath)
    print(f"  Saved to {filepath}")
    return filepath


def clean_gutenberg_text(text: str, start_marker: str) -> str:
    """Strip Project Gutenberg header and footer boilerplate."""
    start = text.find(start_marker)
    end = text.rfind("End of the Project Gutenberg")
    if start == -1:
        start = 0
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def load_book(book: dict, data_dir: str) -> list[Document]:
    """Load, clean, and return a book as a list of Documents with metadata."""
    filepath = download_book(book, data_dir)
    loader = TextLoader(filepath, encoding="utf-8")
    docs = loader.load()
    cleaned = clean_gutenberg_text(docs[0].page_content, book["start_marker"])
    # Attach source metadata to each document
    return [Document(page_content=cleaned, metadata={"source": book["title"]})]


def ingest():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )

    all_chunks = []

    print("\n=== Austen AI - Ingestion Pipeline ===\n")
    print("Step 1: Loading & chunking all novels...")

    for book in AUSTEN_BOOKS:
        docs = load_book(book, data_dir)
        chunks = splitter.split_documents(docs)
        # Preserve source metadata on every chunk
        for chunk in chunks:
            chunk.metadata["source"] = book["title"]
        all_chunks.extend(chunks)
        print(f"  {book['title']}: {len(chunks)} chunks")

    print(f"\nTotal chunks across all novels: {len(all_chunks)}")

    print("\nStep 2: Initialising ChromaDB...")
    embeddings = OllamaEmbeddings(model=settings.embed_model)

    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=settings.chroma_path,
        collection_name=settings.collection_name,
    )

    print("\nStep 3: Embedding & storing chunks...")
    batch_size = 100

    with tqdm(total=len(all_chunks), desc="Embedding", unit="chunk", colour="green") as pbar:
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i : i + batch_size]
            vectorstore.add_documents(batch)
            pbar.update(len(batch))

    print(f"\n✓ Ingestion complete! {len(all_chunks)} chunks stored in {settings.chroma_path}")
    print("  Collection:", settings.collection_name)


if __name__ == "__main__":
    ingest()